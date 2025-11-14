import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models.image import Image
import user_pipeline.main as user_pipeline
import inference_pipeline.main as inference_pipeline
from settings_config import SETTINGS
from db_utils import create_run, create_pending_run, update_run_with_results, update_run_with_error
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

@app.route('/settings', methods=['GET'])
def get_settings():
    settings_list = []
    for key, value in SETTINGS.items():
        settings_list.append({
            'name': key,
            'category': value['category'],
            'image_url': value['image']
        })
    return jsonify({'settings': settings_list}), 200


@app.route('/assets/backgrounds/<filename>', methods=['GET'])
def serve_background_image(filename):
    return send_from_directory(ASSETS_FOLDER, filename)


@app.route('/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    try:
        from db_utils import supabase
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
    try:
        from db_utils import supabase
        result = supabase.table('runs').select('inputs,outputs').eq('is_sample', True).execute()

        samples = []
        for row in result.data:
            samples.append({
                'inputs': row.get('inputs'),
                'outputs': row.get('outputs')
            })

        return jsonify(samples), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _run_generation_worker(run_id, person_img, bgr_result, clothing_imgs, setting_types):
    """
    Worker function that runs the generation pipeline in a background thread.
    Updates progress tracker and Supabase database upon completion.
    """
    try:
        # Run the pipeline with progress tracking
        pipeline_result = inference_pipeline.run(
            bgr_person_image=bgr_result,
            person_image=person_img,
            clothing_images=clothing_imgs,
            setting_types=setting_types,
            run_id=run_id,
            progress_callback=progress_tracker.update_progress
        )

        # Update Supabase with the results
        update_run_with_results(
            run_id=run_id,
            intermediate_outputs=pipeline_result['intermediate_outputs'],
            outputs=pipeline_result['outputs']
        )

        # Mark as complete in progress tracker
        progress_tracker.mark_complete(run_id)

    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()

        # Update both Supabase and progress tracker with error
        try:
            update_run_with_error(run_id, error_msg)
        except Exception as db_error:
            print(f"Failed to update database with error: {db_error}")

        progress_tracker.mark_error(run_id, error_msg)


@app.route('/check_progress', methods=['POST'])
def check_progress():
    """
    Check the progress of one or more generation runs.

    Request body:
        {
            "run_ids": ["uuid1", "uuid2", ...]
        }

    Response:
        {
            "progress": {
                "uuid1": {
                    "progress": 45,
                    "is_complete": false,
                    "error": null
                },
                "uuid2": {
                    "progress": 100,
                    "is_complete": true,
                    "error": null
                }
            }
        }
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

        # Format response
        response = {}
        for run_id, run_progress in progress_data.items():
            if run_progress is None:
                # Run not found in progress tracker - might be old or not started
                response[run_id] = {
                    'progress': 0,
                    'is_complete': False,
                    'error': 'Run not found in progress tracker'
                }
            else:
                response[run_id] = {
                    'progress': run_progress.progress,
                    'is_complete': run_progress.is_complete,
                    'error': run_progress.error
                }

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
        setting_types = json.loads(settings_json)

        if not isinstance(setting_types, list) or len(setting_types) == 0:
            return jsonify({'error': 'Settings must be a non-empty array'}), 400
        if len(setting_types) > 3:
            return jsonify({'error': 'Maximum 3 settings allowed'}), 400

        for st in setting_types:
            if st not in SETTINGS:
                return jsonify({'error': f'Invalid setting type: {st}'}), 400

        # Process images and upload them
        person_img = Image(filepath=person_file)
        bgr_result = user_pipeline.run(person_img)
        clothing_imgs = [Image(filepath=f) for f in clothing_files]

        # Create pending run in database immediately
        run_id = create_pending_run(
            model_url=person_img.url,
            clothing_url=clothing_imgs[0].url if clothing_imgs else None,
            settings=setting_types
        )

        # Initialize progress tracker
        progress_tracker.create_run(run_id)

        # Start background thread for generation
        thread = threading.Thread(
            target=_run_generation_worker,
            args=(run_id, person_img, bgr_result, clothing_imgs, setting_types)
        )
        thread.daemon = True
        thread.start()

        # Return run_id immediately
        return jsonify({'run_id': run_id}), 202  # 202 Accepted

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Flask development server supports multiple concurrent requests by default
    # For production, use a WSGI server like Gunicorn with multiple workers
    app.run(debug=True, host='0.0.0.0', port=4000, threaded=True)
