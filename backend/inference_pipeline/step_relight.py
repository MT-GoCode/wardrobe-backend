import concurrent.futures
from ai_api_utils.fal_ai import create_prediction, poll_prediction


def relight_single(image_url, setting, gender):
    prompt = f"{gender} in {setting['setting']} with {setting['lighting']}"

    input_payload = {
        "prompt": prompt,
        "image_url": image_url,
        "light_source_position": "left",
        "cfg_scale": 2,
        "lower_denoise": 1.0,
        "highres_denoise": 1.0,
        "guidance_scale": 9
    }

    model_path = "fal-ai/iclight-v2"
    result = create_prediction(model_path, input_payload)

    import sys
    sys.stdout.write(f"Fal.ai result: {result}\n")
    sys.stdout.flush()

    # Fal.ai returns results immediately, not a request_id
    if 'images' in result and result['images']:
        return {
            'image_url': result['images'][0]['url'],
            'setting': setting
        }

    sys.stdout.write(f"ERROR: No images found in fal.ai response: {result}\n")
    sys.stdout.flush()
    return None


def relight(vton_results):
    if not vton_results:
        return []

    max_workers = min(len(vton_results), 10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(relight_single, item['image_url'], item['setting'], item['setting']['gender']): item
            for item in vton_results
        }

        results = []
        for future in concurrent.futures.as_completed(future_to_item):
            try:
                result = future.result()
                if result:
                    results.append(result)
                    import sys
                    sys.stdout.write(f"Added relit image: {result['image_url']}\n")
                    sys.stdout.flush()
            except Exception as e:
                import sys
                sys.stdout.write(f"Relight request failed: {str(e)}\n")
                sys.stdout.flush()

    return results
