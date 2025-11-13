import uuid


def generate_uuid_filename(extension='png'):
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{extension}"
