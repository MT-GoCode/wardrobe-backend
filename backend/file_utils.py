import os
import requests
from PIL import Image
import io


TEMP_FOLDER = 'temp'


def ensure_temp_folder():
    os.makedirs(TEMP_FOLDER, exist_ok=True)


def save_image_locally(image_data, filename):
    ensure_temp_folder()
    try:
        if hasattr(image_data, 'read'):
            img_bytes = image_data.read()
            image_data.seek(0)
        else:
            img_bytes = image_data

        img = Image.open(io.BytesIO(img_bytes))

        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        if not filename.endswith('.png'):
            filename = filename.rsplit('.', 1)[0] + '.png'

        filepath = os.path.join(TEMP_FOLDER, filename)
        img.save(filepath, format='PNG', optimize=True)

        return filepath
    except Exception as e:
        raise Exception(f"Failed to save image locally: {str(e)}")


def download_image_from_url(url, filename):
    ensure_temp_folder()
    try:
        response = requests.get(url, timeout=600)
        response.raise_for_status()
        return save_image_locally(response.content, filename)
    except Exception as e:
        raise Exception(f"Failed to download image from URL: {str(e)}")


def clear_temp_folder():
    ensure_temp_folder()
    for filename in os.listdir(TEMP_FOLDER):
        filepath = os.path.join(TEMP_FOLDER, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
