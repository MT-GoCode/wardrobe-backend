from .step_analyze import analyze
from .step_repose import repose
from .step_vton import vton
from .step_relight import relight
from .step_enhance import enhance
from models.image import Image


def run(bgr_person_image, person_image, clothing_images, setting_types):
    person_url = person_image.url
    bgr_url = bgr_person_image.url
    clothing_urls = [img.url for img in clothing_images]

    analysis_result = analyze(person_url, clothing_urls, setting_types)
    gender = analysis_result['gender']
    clothing_type = analysis_result['clothing_type']
    settings = analysis_result['settings']

    repose_results = repose(bgr_url, settings, gender)
    vton_results = vton(repose_results, clothing_urls, gender, clothing_type)
    relight_results = relight(vton_results)
    enhance_results = enhance(relight_results)

    final_images = []
    for result in enhance_results:
        final_images.append(Image(url=result['image_url'], filepath=None))

    intermediate_outputs = {
        'step_analyze': analysis_result,
        'step_repose': repose_results,
        'step_vton': vton_results,
        'step_relight': relight_results,
        'step_enhance': enhance_results
    }

    return {
        'analysis': analysis_result,
        'intermediate_outputs': intermediate_outputs,
        'outputs': final_images
    }
