import json
from .step_analyze import analyze
from .step_repose import repose
from .step_vton import vton
from .step_relight import relight
from .step_enhance import enhance
from models.image import Image


def run(bgr_person_image, person_image, clothing_images):
    person_url = person_image.url
    bgr_url = bgr_person_image.url
    clothing_urls = [img.url for img in clothing_images]

    with open('dump.txt', 'w') as f:
        f.write("="*80 + "\n")
        f.write("INFERENCE PIPELINE RUN\n")
        f.write("="*80 + "\n\n")

    analysis_result = analyze(person_url, clothing_urls)

    with open('dump.txt', 'a') as f:
        f.write("="*80 + "\n")
        f.write("STEP 1: ANALYSIS\n")
        f.write("="*80 + "\n")
        f.write(f"Gender: {analysis_result.get('gender')}\n")
        f.write(f"Clothing Type: {analysis_result.get('clothing_type')}\n")
        f.write(f"Number of Settings: {len(analysis_result.get('settings', []))}\n")
        f.write("\nFull Analysis:\n")
        f.write(json.dumps(analysis_result, indent=2))
        f.write("\n\n")

    gender = analysis_result['gender']
    clothing_type = analysis_result['clothing_type']
    settings = analysis_result['settings']

    repose_results = repose(bgr_url, settings, gender)

    with open('dump.txt', 'a') as f:
        f.write("="*80 + "\n")
        f.write("STEP 2: REPOSE\n")
        f.write("="*80 + "\n")
        f.write(f"Number of Reposed Images: {len(repose_results)}\n")
        for i, result in enumerate(repose_results):
            f.write(f"\n  Image {i+1}:\n")
            f.write(f"    URL: {result.get('image_url')}\n")
            f.write(f"    Pose: {result.get('setting', {}).get('pose')}\n")
        f.write("\n\nFull Repose Results:\n")
        f.write(json.dumps(repose_results, indent=2))
        f.write("\n\n")

    vton_results = vton(repose_results, clothing_urls, gender, clothing_type)

    with open('dump.txt', 'a') as f:
        f.write("="*80 + "\n")
        f.write("STEP 3: VTON\n")
        f.write("="*80 + "\n")
        f.write(f"Number of VTON Images: {len(vton_results)}\n")
        for i, result in enumerate(vton_results):
            f.write(f"\n  Image {i+1}:\n")
            f.write(f"    URL: {result.get('image_url')}\n")
            f.write(f"    Clothing: {clothing_type}\n")
        f.write("\n\nFull VTON Results:\n")
        f.write(json.dumps(vton_results, indent=2))
        f.write("\n\n")

    relight_results = relight(vton_results)

    with open('dump.txt', 'a') as f:
        f.write("="*80 + "\n")
        f.write("STEP 4: RELIGHT\n")
        f.write("="*80 + "\n")
        f.write(f"Number of Relit Images: {len(relight_results)}\n")
        for i, result in enumerate(relight_results):
            f.write(f"\n  Image {i+1}:\n")
            f.write(f"    URL: {result.get('image_url')}\n")
            f.write(f"    Lighting: {result.get('setting', {}).get('lighting')}\n")
        f.write("\n\nFull Relight Results:\n")
        f.write(json.dumps(relight_results, indent=2))
        f.write("\n\n")

    enhance_results = enhance(relight_results)

    with open('dump.txt', 'a') as f:
        f.write("="*80 + "\n")
        f.write("STEP 5: ENHANCE\n")
        f.write("="*80 + "\n")
        f.write(f"Number of Enhanced Images: {len(enhance_results)}\n")
        for i, result in enumerate(enhance_results):
            f.write(f"\n  Image {i+1}:\n")
            f.write(f"    URL: {result.get('image_url')}\n")
        f.write("\n\nFull Enhance Results:\n")
        f.write(json.dumps(enhance_results, indent=2))
        f.write("\n\n")
        f.write("="*80 + "\n")
        f.write("PIPELINE COMPLETE\n")
        f.write("="*80 + "\n")

    final_images = []
    for result in enhance_results:
        final_images.append(Image(url=result['image_url'], filepath=None))

    return {
        'analysis': analysis_result,
        'final_images': final_images
    }
