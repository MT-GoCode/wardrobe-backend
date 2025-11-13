import os
from supabase import create_client, Client
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

# Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'uploads')

supabase: Client = create_client(supabase_url, supabase_key)


def upload_image_to_supabase(image_file, filename):
    try:
        if hasattr(image_file, 'read'):
            image_data = image_file.read()
            image_file.seek(0)
        else:
            image_data = image_file

        img = Image.open(io.BytesIO(image_data))

        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        if not filename.endswith('.png'):
            filename = filename.rsplit('.', 1)[0] + '.png'

        response = supabase.storage.from_(bucket_name).upload(
            filename,
            buffer.getvalue(),
            file_options={"content-type": "image/png"}
        )

        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)

        return public_url

    except Exception as e:
        raise Exception(f"Failed to upload to Supabase: {str(e)}")


def delete_image_from_supabase(filename):
    try:
        supabase.storage.from_(bucket_name).remove([filename])
        return True
    except Exception as e:
        raise Exception(f"Failed to delete from Supabase: {str(e)}")
