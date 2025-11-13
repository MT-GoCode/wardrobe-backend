from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from general_utils import generate_uuid_filename
from db_utils import upload_image_to_supabase
from file_utils import save_image_locally
from models.image import Image
from user_pipeline.main import run as run_user_pipeline
from inference_pipeline.main import run as run_inference_pipeline

load_dotenv()

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return jsonify({'status': 'Wardrobe Backend API Running'})


@app.route('/generate_request', methods=['POST'])
def generate_request():
    try:
        if 'person_image' not in request.files:
            return jsonify({'error': 'No person image provided'}), 400

        person_image = request.files['person_image']
        clothing_images = request.files.getlist('clothing_images')

        if person_image.filename == '':
            return jsonify({'error': 'No person image selected'}), 400

        if not clothing_images or all(img.filename == '' for img in clothing_images):
            return jsonify({'error': 'No clothing images selected'}), 400

        if not allowed_file(person_image.filename):
            return jsonify({'error': 'Invalid person image file type'}), 400

        for clothing_image in clothing_images:
            if clothing_image.filename != '' and not allowed_file(clothing_image.filename):
                return jsonify({'error': f'Invalid clothing image file type: {clothing_image.filename}'}), 400

        valid_clothing_images = [img for img in clothing_images if img.filename != '']

        # Process person image
        person_filename = generate_uuid_filename()
        person_url = upload_image_to_supabase(person_image, person_filename)
        person_image.seek(0)
        person_filepath = save_image_locally(person_image, person_filename)
        person_img = Image(url=person_url, filepath=person_filepath)

        # Process clothing images
        clothing_imgs = []
        for clothing_image in valid_clothing_images:
            filename = generate_uuid_filename()
            url = upload_image_to_supabase(clothing_image, filename)
            clothing_image.seek(0)
            filepath = save_image_locally(clothing_image, filename)
            clothing_imgs.append(Image(url=url, filepath=filepath))

        # Run user pipeline on person image
        bgr_result = run_user_pipeline(person_img)
        import sys
        sys.stdout.write(f"Background removal result: {bgr_result}\n")
        sys.stdout.flush()

        # Run inference pipeline
        inference_result = run_inference_pipeline(bgr_result, person_img, clothing_imgs)
        sys.stdout.write(f"Inference result: {inference_result}\n")
        sys.stdout.flush()

        final_images = inference_result.get('final_images', [])

        return jsonify({
            'message': 'Images processed successfully',
            'person': {
                'filename': person_filename,
                'url': person_url,
                'local_path': person_filepath
            },
            'clothing': [
                {
                    'url': img.url,
                    'local_path': img.filepath
                }
                for img in clothing_imgs
            ],
            'bgr_result': {
                'url': bgr_result.url,
                'filepath': bgr_result.filepath
            },
            'final_images': [img.to_dict() for img in final_images]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
