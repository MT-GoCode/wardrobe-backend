import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models.image import Image
import inference_pipeline.main as inference_pipeline
from db_utils import (
    create_pending_run, 
    update_run_with_results, 
    update_run_with_error,
    get_all_presets,
    get_preset_names_by_ids,
    supabase
)
from progress_tracker import progress_tracker

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ASSETS_FOLDER = 'assets/backgrounds'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ASSETS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


@app.route('/presets', methods=['GET'])
def get_presets():
    """
    Get all available presets.
    
    Returns:
        List of presets with id, name, and ref_image_background_only
    """
    try:
        presets = get_all_presets()
        return jsonify({'presets': presets}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/assets/backgrounds/<filename>', methods=['GET'])
def serve_background_image(filename):
    return send_from_directory(ASSETS_FOLDER, filename)


@app.route('/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    try:
        result = supabase.table('runs').select('*').eq('id', run_id).execute()

        if not result.data or len(result.data) == 0:
            return jsonify({'error': 'Run not found'}), 404

        return jsonify(result.data[0]), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/sample_generations', methods=['GET'])
def get_sample_generations():
    """
    Get sample generations with preset IDs decoded to names.
    """
    try:
        result = supabase.table('runs').select('inputs,outputs').eq('is_sample', True).execute()

        samples = []
        for row in result.data:
            inputs = row.get('inputs', {})
            outputs = row.get('outputs', [])
            
            # Decode preset IDs to names if present
            preset_ids = inputs.get('settings', [])
            if preset_ids and isinstance(preset_ids[0], int):
                # These are numeric IDs, decode to names
                preset_names_map = get_preset_names_by_ids(preset_ids)
                preset_names = [preset_names_map.get(pid, str(pid)) for pid in preset_ids]
                inputs = {**inputs, 'settings': preset_names}
            
            samples.append({
                'inputs': inputs,
                'outputs': outputs
            })

        return jsonify(samples), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _run_generation_worker(run_id, run_id_str, person_img, clothing_img, preset_ids):
    """
    Worker function that runs the generation pipeline in a background thread.
    Updates progress tracker and Supabase database upon completion.
    
    Args:
        run_id: Integer run ID for database operations
        run_id_str: String run ID for progress tracker
    """
    try:
        # Create progress callback that uses string run_id
        # Signature: callback(progress) - run_id_str is captured in closure
        def progress_callback(progress):
            progress_tracker.update_progress(run_id_str, progress)
        
        # Run the pipeline with progress tracking
        pipeline_result = inference_pipeline.run(
            person_image=person_img,
            clothing_image=clothing_img,
            preset_ids=preset_ids,
            run_id=run_id_str,  # Pass string for callback
            progress_callback=progress_callback
        )

        # Update Supabase with the results (use integer run_id)
        update_run_with_results(
            run_id=run_id,
            intermediate_outputs=pipeline_result['intermediate_outputs'],
            outputs=pipeline_result['outputs']
        )

        # Mark as complete in progress tracker (use string run_id)
        progress_tracker.mark_complete(run_id_str)

    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()

        # Update both Supabase and progress tracker with error
        try:
            update_run_with_error(run_id, error_msg)  # Integer for database
        except Exception as db_error:
            print(f"Failed to update database with error: {db_error}")

        progress_tracker.mark_error(run_id_str, error_msg)  # String for tracker


@app.route('/check_progress', methods=['POST'])
def check_progress():
    """
    Check the progress of one or more generation runs.
    
    Progress Tracking System:
    - When a generation starts, a run is created in the database (returns integer ID)
    - The progress tracker stores progress in memory using string keys
    - Client sends run_ids as strings in the request
    - Progress is updated by the background worker thread as the pipeline runs
    - Once complete, results are saved to database and progress tracker marks it complete

    Request body:
        {
            "run_ids": ["27", "28", ...]  # String IDs
        }

    Response:
        {
            "progress": {
                "27": {
                    "progress": 45,
                    "is_complete": false,
                    "error": null
                },
                "28": {
                    "progress": 100,
                    "is_complete": true,
                    "error": null
                }
            }
        }
    
    Error codes:
        - 200: Success, all runs found and no errors
        - 400: Bad request (invalid input)
        - 404: All requested runs not found
        - 500: Server error or runs have failed with errors
    """
    try:
        data = request.get_json()

        if not data or 'run_ids' not in data:
            return jsonify({'error': 'run_ids array required in request body'}), 400

        run_ids = data['run_ids']

        if not isinstance(run_ids, list):
            return jsonify({'error': 'run_ids must be an array'}), 400

        if len(run_ids) == 0:
            return jsonify({'error': 'run_ids array cannot be empty'}), 400

        if len(run_ids) > 50:
            return jsonify({'error': 'Maximum 50 run_ids allowed per request'}), 400

        # Get progress for all requested runs
        progress_data = progress_tracker.get_multiple_progress(run_ids)

        # Check if progress tracker itself failed (all None)
        if progress_data is None or all(p is None for p in progress_data.values()):
            return jsonify({'error': 'Failed to retrieve progress from database'}), 500

        # Format response and check for errors
        response = {}
        has_errors = False
        all_not_found = True

        for run_id, run_progress in progress_data.items():
            if run_progress is None:
                # Run not found in database
                response[run_id] = {
                    'progress': 0,
                    'is_complete': False,
                    'error': 'Run not found'
                }
            else:
                all_not_found = False
                # Check if this run has an error
                if run_progress.error:
                    has_errors = True
                
                response[run_id] = {
                    'progress': run_progress.progress,
                    'is_complete': run_progress.is_complete,
                    'error': run_progress.error
                }

        # Return appropriate status codes
        if all_not_found:
            return jsonify({'error': 'All requested runs not found', 'progress': response}), 404
        
        if has_errors:
            # At least one run has failed with an error
            return jsonify({'error': 'One or more runs have failed', 'progress': response}), 500

        # All runs found and no errors
        return jsonify({'progress': response}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/generate_request', methods=['POST'])
def generate_request():
    """
    Create a new generation request. Immediately returns a run_id and starts
    processing in the background. Clients should poll /check_progress to monitor
    progress and then fetch results from /runs/<run_id> when complete.
    
    Expected form data:
        - personImage: File - the model/person image
        - clothingImages: File(s) - the clothing image(s) (only first one is used)
        - settings: JSON string - array of preset IDs (integers)
    """
    try:
        if 'personImage' not in request.files:
            return jsonify({'error': 'No person image provided'}), 400
        if 'clothingImages' not in request.files:
            return jsonify({'error': 'No clothing images provided'}), 400
        if 'settings' not in request.form:
            return jsonify({'error': 'No settings provided'}), 400

        person_file = request.files['personImage']
        clothing_files = request.files.getlist('clothingImages')
        settings_json = request.form['settings']

        import json
        try:
            preset_ids = json.loads(settings_json)
        except json.JSONDecodeError as json_error:
            return jsonify({'error': f'Invalid JSON in settings: {str(json_error)}'}), 400

        if not isinstance(preset_ids, list) or len(preset_ids) == 0:
            return jsonify({'error': 'Settings must be a non-empty array of preset IDs'}), 400
        if len(preset_ids) > 3:
            return jsonify({'error': 'Maximum 3 presets allowed'}), 400
        
        # Validate that all preset IDs are integers
        for pid in preset_ids:
            if not isinstance(pid, int):
                return jsonify({'error': f'Invalid preset ID: {pid}. Must be an integer.'}), 400

        # Process images and upload them
        try:
            person_img = Image(filepath=person_file)
            # Only use the first clothing image
            clothing_img = Image(filepath=clothing_files[0])
        except Exception as img_error:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to process images: {str(img_error)}'}), 500

        # Create pending run in database immediately
        try:
            run_id = create_pending_run(
                model_url=person_img.url,
                clothing_url=clothing_img.url,
                settings=preset_ids  # Now storing numeric IDs
            )
        except Exception as db_error:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to create run in database: {str(db_error)}'}), 500
        
        # Convert run_id to string for consistency (database returns int, tracker uses str keys)
        run_id_str = str(run_id)

        # Initialize progress tracker
        try:
            progress_tracker.create_run(run_id_str)
        except Exception as tracker_error:
            import traceback
            traceback.print_exc()
            # Run was created but progress tracking failed - still return the run_id
            # but log the error (the worker thread will handle progress updates)
            print(f"Warning: Failed to initialize progress tracker for run {run_id_str}: {tracker_error}")

        # Start background thread for generation
        # Pass run_id_str to worker for progress tracking, but keep run_id (int) for database
        try:
            thread = threading.Thread(
                target=_run_generation_worker,
                args=(run_id, run_id_str, person_img, clothing_img, preset_ids)
            )
            thread.daemon = True
            thread.start()
        except Exception as thread_error:
            import traceback
            traceback.print_exc()
            # Run was created but thread failed to start - mark as error
            try:
                update_run_with_error(run_id, f'Failed to start generation thread: {str(thread_error)}')
                progress_tracker.mark_error(run_id_str, f'Failed to start generation thread: {str(thread_error)}')
            except Exception as update_error:
                print(f"Failed to update run with thread error: {update_error}")
            return jsonify({'error': f'Failed to start generation: {str(thread_error)}'}), 500

        # Return run_id (int) immediately - client will convert to string when checking progress
        return jsonify({'run_id': run_id}), 202  # 202 Accepted

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# Development server - only used when running: python app.py
# In production, Gunicorn runs the app (see /etc/systemd/system/wardrobe.service)
# The port 4000 here is irrelevant in production - Gunicorn binds to 127.0.0.1:8000
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000, threaded=True)
