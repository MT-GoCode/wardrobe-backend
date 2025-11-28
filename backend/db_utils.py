import os
from supabase import create_client, Client
from dotenv import load_dotenv
from PIL import Image as PILImage
import io

load_dotenv()

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

        img = PILImage.open(io.BytesIO(image_data))

        if img.mode in ('RGBA', 'LA', 'P'):
            background = PILImage.new('RGB', img.size, (255, 255, 255))
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


def serialize_value(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return {k: serialize_value(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: serialize_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_value(item) for item in obj]
    else:
        return obj


def create_run(model_url, clothing_url, intermediate_outputs, outputs, settings):
    """Legacy function for backward compatibility. Creates a complete run."""
    inputs = {
        "model": model_url,
        "clothing": clothing_url,
        "settings": settings
    }

    outputs_json = [serialize_value(img) for img in outputs]
    intermediate_json = serialize_value(intermediate_outputs)

    result = supabase.table('runs').insert({
        'is_sample': False,
        'inputs': inputs,
        'intermediate_outputs': intermediate_json,
        'outputs': outputs_json,
        'status': 'completed'
    }).execute()

    if result.data and len(result.data) > 0:
        return result.data[0]['id']
    else:
        raise Exception("Failed to create run in database")


def create_pending_run(model_url, clothing_url, settings):
    """
    Create a new run in 'pending' status without outputs.
    This is called immediately when a generation request is received.

    Returns:
        str: The run_id of the created run
    """
    inputs = {
        "model": model_url,
        "clothing": clothing_url,
        "settings": settings
    }

    result = supabase.table('runs').insert({
        'is_sample': False,
        'inputs': inputs,
        'intermediate_outputs': None,
        'outputs': None,
        'status': 'pending'
    }).execute()

    if result.data and len(result.data) > 0:
        return result.data[0]['id']
    else:
        raise Exception("Failed to create pending run in database")


def update_run_with_results(run_id, intermediate_outputs, outputs):
    """
    Update a run with the final results after generation completes.

    Args:
        run_id: The ID of the run to update
        intermediate_outputs: The intermediate outputs from the pipeline
        outputs: The final output images
    """
    outputs_json = [serialize_value(img) for img in outputs]
    intermediate_json = serialize_value(intermediate_outputs)

    result = supabase.table('runs').update({
        'intermediate_outputs': intermediate_json,
        'outputs': outputs_json,
        'status': 'completed'
    }).eq('id', run_id).execute()

    if not result.data or len(result.data) == 0:
        raise Exception(f"Failed to update run {run_id} in database")


def update_run_with_error(run_id, error_message):
    """
    Update a run with error status when generation fails.

    Args:
        run_id: The ID of the run to update
        error_message: The error message to store
    """
    result = supabase.table('runs').update({
        'status': 'failed',
        'error': error_message
    }).eq('id', run_id).execute()

    if not result.data or len(result.data) == 0:
        raise Exception(f"Failed to update run {run_id} with error")


def get_all_presets():
    """
    Get all presets from the presets table.
    
    Returns:
        List of dicts with 'id', 'name', 'ref_image_background_only'
    """
    result = supabase.table('presets').select('id, name, ref_image_background_only').execute()
    
    if result.data:
        return result.data
    return []


def get_preset_names_by_ids(preset_ids):
    """
    Get preset names for a list of preset IDs.
    
    Args:
        preset_ids: List of preset IDs (integers)
        
    Returns:
        Dict mapping preset_id to preset name
    """
    if not preset_ids:
        return {}
    
    result = supabase.table('presets').select('id, name').in_('id', preset_ids).execute()
    
    if result.data:
        return {row['id']: row['name'] for row in result.data}
    return {}
