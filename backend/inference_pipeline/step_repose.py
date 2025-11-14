import asyncio
import concurrent.futures
from ai_api_utils.wavespeed import create_prediction, poll_prediction


def repose_single(bgr_image_url, setting, gender):
    prompt = f"The {gender} has pose {setting['pose']}, with exact same face, realistic skin with imperfections, realistic eyes, exact same facial identity, exact same clothing, exact same details, correct body structure"

    input_payload = {
        "prompt": prompt,
        "images": [bgr_image_url],
        "enable_sync_mode": False,
        "enable_base64_output": False,
        "num_inference_steps": 35,
        "guidance_scale": 8
    }

    model_path = "bytedance/seedream-v4/edit"
    creation_result = create_prediction(model_path, input_payload)

    import sys
    sys.stdout.write(f"Wavespeed creation result: {creation_result}\n")
    sys.stdout.flush()

    prediction_id = creation_result.get('id') or creation_result.get('data', {}).get('id')

    if not prediction_id:
        sys.stdout.write(f"ERROR: No prediction ID found in response: {creation_result}\n")
        sys.stdout.flush()

    return prediction_id


def repose(bgr_image_url, settings, gender):
    if not settings:
        return []

    max_workers = min(len(settings), 10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_setting = {
            executor.submit(repose_single, bgr_image_url, setting, gender): setting
            for setting in settings
        }

        prediction_ids = []
        for future in concurrent.futures.as_completed(future_to_setting):
            setting = future_to_setting[future]
            try:
                prediction_id = future.result()
                prediction_ids.append({
                    'prediction_id': prediction_id,
                    'setting': setting
                })
            except Exception as e:
                print(f"Repose request failed for setting {setting['id']}: {str(e)}")

    results = []
    for item in prediction_ids:
        try:
            import sys
            sys.stdout.write(f"Polling prediction {item['prediction_id']}...\n")
            sys.stdout.flush()

            final_result = poll_prediction(item['prediction_id'])

            sys.stdout.write(f"Got result: {final_result}\n")
            sys.stdout.flush()

            output_urls = final_result.get('output') or final_result.get('outputs') or final_result.get('data', {}).get('outputs')

            if output_urls:
                url = output_urls[0] if isinstance(output_urls, list) else output_urls
                results.append({
                    'image_url': url,
                    'setting': item['setting']
                })
                sys.stdout.write(f"Added image URL: {url}\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"Polling failed for prediction {item['prediction_id']}: {str(e)}\n")
            sys.stdout.flush()

    return results
