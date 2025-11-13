class Image:
    def __init__(self, url=None, filepath=None):
        self.url = url
        self.filepath = filepath

    def __repr__(self):
        return f"Image(url={self.url}, filepath={self.filepath})"

    def to_dict(self):
        return {
            'url': self.url,
            'filepath': self.filepath
        }
