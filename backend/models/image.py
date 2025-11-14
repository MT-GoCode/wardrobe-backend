from db_utils import upload_image_to_supabase
from general_utils import generate_uuid_filename

class Image:
    def __init__(self, url=None, filepath=None):
        if filepath:
            filename = generate_uuid_filename()
            self.url = upload_image_to_supabase(filepath, filename)
            self.filepath = filename
        else:
            self.url = url
            self.filepath = filepath

    def __repr__(self):
        return f"Image(url={self.url}, filepath={self.filepath})"

    def to_dict(self):
        return {
            'url': self.url,
            'filepath': self.filepath
        }
