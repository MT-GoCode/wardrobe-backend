import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models.image import Image
import user_pipeline.main as user_pipeline
import inference_pipeline.main as inference_pipeline
from settings_config import SETTINGS
from db_utils import create_run

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


@app.route('/generate_request', methods=['POST'])
def generate_request():
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

        person_img = Image(filepath=person_file)
        bgr_result = user_pipeline.run(person_img)
        clothing_imgs = [Image(filepath=f) for f in clothing_files]

        pipeline_result = inference_pipeline.run(
            bgr_person_image=bgr_result,
            person_image=person_img,
            clothing_images=clothing_imgs,
            setting_types=setting_types
        )

        run_id = create_run(
            model_url=person_img.url,
            clothing_url=clothing_imgs[0].url if clothing_imgs else None,
            intermediate_outputs=pipeline_result['intermediate_outputs'],
            outputs=pipeline_result['outputs'],
            settings=setting_types
        )

        return jsonify({'run_id': run_id}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Flask development server supports multiple concurrent requests by default
    # For production, use a WSGI server like Gunicorn with multiple workers
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
