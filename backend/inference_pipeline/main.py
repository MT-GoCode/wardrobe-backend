from .step_analyze import analyze
from .step_repose import repose
from .step_vton import vton
from .step_relight import relight
from .step_enhance import enhance
from models.image import Image


def run(bgr_person_image, person_image, clothing_images, setting_types, run_id=None, progress_callback=None):
    """
    Run the inference pipeline with optional progress tracking.

    Args:
        bgr_person_image: Background-removed person image
        person_image: Original person image
        clothing_images: List of clothing images
        setting_types: List of setting types
        run_id: Optional run ID for progress tracking
        progress_callback: Optional callback function(run_id, progress) to update progress

    Returns:
        Dict with analysis, intermediate_outputs, and outputs
    """
    person_url = person_image.url
    bgr_url = bgr_person_image.url
    clothing_urls = [img.url for img in clothing_images]

    def update_progress(progress):
        """Helper to update progress if callback is provided."""
        if progress_callback and run_id:
            progress_callback(run_id, progress)

    # Stage 1: Analyze (0% -> 20%)
    update_progress(0)
    analysis_result = analyze(person_url, clothing_urls, setting_types)
    gender = analysis_result['gender']
    clothing_type = analysis_result['clothing_type']
    settings = analysis_result['settings']
    update_progress(20)

    # Stage 2: Repose (20% -> 40%)
    repose_results = repose(bgr_url, settings, gender)
    update_progress(40)

    # Stage 3: VTON (40% -> 60%)
    vton_results = vton(repose_results, clothing_urls, gender, clothing_type)
    update_progress(60)

    # Stage 4: Relight (60% -> 80%)
    relight_results = relight(vton_results)
    update_progress(80)

    # Stage 5: Enhance (80% -> 100%)
    enhance_results = enhance(relight_results)
    update_progress(100)

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
