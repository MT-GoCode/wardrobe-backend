import concurrent.futures
from ai_api_utils.wavespeed import create_prediction, poll_prediction


def vton_single(reposed_image_url, clothing_image_urls, setting, gender, clothing_type):
    prompt = f"a photo of the {gender} wearing the exact {clothing_type}, same pose, with exact same face, exact same eyes, exact same facial identity, exact same {clothing_type}, exact same body structure, exact same details in the {clothing_type}, exact same colors in {clothing_type}, exact same texture in {clothing_type}, correct realistic face, correct body structure, realistic skin with imperfections, realistic eyes"

    input_payload = {
        "prompt": prompt,
        "images": [reposed_image_url] + clothing_image_urls,
        "enable_sync_mode": False,
        "enable_base64_output": False,
        "num_inference_steps": 35,
        "guidance_scale": 8
    }

    model_path = "bytedance/seedream-v4/edit"
    creation_result = create_prediction(model_path, input_payload)

    import sys
    sys.stdout.write(f"VTON Wavespeed creation result: {creation_result}\n")
    sys.stdout.flush()

    prediction_id = creation_result.get('id') or creation_result.get('data', {}).get('id')

    if not prediction_id:
        sys.stdout.write(f"ERROR: No prediction ID found in VTON response: {creation_result}\n")
        sys.stdout.flush()

    return prediction_id


def vton(repose_results, clothing_image_urls, gender, clothing_type):
    if not repose_results:
        return []

    max_workers = min(len(repose_results), 10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(vton_single, item['image_url'], clothing_image_urls, item['setting'], gender, clothing_type): item
            for item in repose_results
        }

        prediction_ids = []
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                prediction_id = future.result()
                prediction_ids.append({
                    'prediction_id': prediction_id,
                    'setting': item['setting']
                })
            except Exception as e:
                print(f"VTON request failed for setting {item['setting']['id']}: {str(e)}")

    results = []
    for item in prediction_ids:
        try:
            import sys
            sys.stdout.write(f"Polling VTON prediction {item['prediction_id']}...\n")
            sys.stdout.flush()

            final_result = poll_prediction(item['prediction_id'])

            sys.stdout.write(f"Got VTON result: {final_result}\n")
            sys.stdout.flush()

            output_urls = final_result.get('output') or final_result.get('outputs') or final_result.get('data', {}).get('outputs')

            if output_urls:
                url = output_urls[0] if isinstance(output_urls, list) else output_urls
                results.append({
                    'image_url': url,
                    'setting': item['setting']
                })
                sys.stdout.write(f"Added VTON image URL: {url}\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"VTON polling failed for prediction {item['prediction_id']}: {str(e)}\n")
            sys.stdout.flush()

    return results
