from .step_bgr import remove_background
from models.image import Image


def run(image):
    bgr_url = remove_background(image.url)
    return Image(url=bgr_url, filepath=None)
