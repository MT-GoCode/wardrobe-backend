import concurrent.futures
from ai_api_utils.wavespeed import create_prediction, poll_prediction
from ai_api_utils.openai_api import vision_completion


def generate_enhancement_prompt(image_url):
    system_prompt = """You are an AI image enhancement specialist. Generate a detailed prompt for enhancing realism in AI-generated images.
Focus on texture, detail, and micro-features while preserving the overall composition.
Do NOT generate an image. Do NOT say or do anything else beyond providing this prompt. Your entire response should be this prompt."""

    prompt = """Analyze this image and return an enhancement prompt similar to these examples:

For a city scene: realistic skin, realistic eyes with pupil glint at camera and white eye whites, correct hands, correct limbs, dry realistic hair with individual strands, with no physical changes to the person, no changes to body structure, no changes to clothing, no changes to lighting, no changes to scenery, sharpen realistic concrete grain and pavement texture, add metallic glint to cars, increase detail of plant foliage, improve roughness of wall texture

For a nature scene: realistic skin, realistic eyes with pupil glint at camera and white eye whites, correct hands, correct limbs, dry realistic hair with individual strands, with no physical changes to the person, no changes to body structure, no changes to clothing, no changes to lighting, no changes to scenery, enhance natural ground texture, sharpen dirt path detail, increase high-frequency detail in grass and foliage, enrich fine leaf edges, add subtle roughness and micro-texture to plants, improve realism of tree bark detail, increase depth and crispness of sunset haze without altering direction or color, preserve overall geometry and composition

Return a similar prompt for this image. First warn against certain changes, then point out specific aspects to increase realism. Your entire response should be only this prompt, nothing else."""

    result = vision_completion(image_url, prompt, system_prompt=system_prompt, max_tokens=300)
    enhancement_prompt = result['choices'][0]['message']['content'].strip()

    return enhancement_prompt


def enhance_single(image_url, setting):
    import sys
    sys.stdout.write(f"Generating enhancement prompt for image...\n")
    sys.stdout.flush()

    enhancement_prompt = generate_enhancement_prompt(image_url)

    sys.stdout.write(f"Enhancement prompt: {enhancement_prompt}\n")
    sys.stdout.flush()

    input_payload = {
        "prompt": "correct eyes, realistic face, " + enhancement_prompt,
        "images": [image_url],
        "enable_sync_mode": False,
        "enable_base64_output": False,
        "num_inference_steps": 35,
        "guidance_scale": 8
    }

    model_path = "bytedance/seedream-v4/edit"
    creation_result = create_prediction(model_path, input_payload)

    sys.stdout.write(f"Enhancement Wavespeed creation result: {creation_result}\n")
    sys.stdout.flush()

    prediction_id = creation_result.get('id') or creation_result.get('data', {}).get('id')

    if not prediction_id:
        sys.stdout.write(f"ERROR: No prediction ID found in enhancement response: {creation_result}\n")
        sys.stdout.flush()

    return prediction_id


def enhance(relight_results):
    if not relight_results:
        return []

    max_workers = min(len(relight_results), 10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(enhance_single, item['image_url'], item['setting']): item
            for item in relight_results
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
                print(f"Enhancement request failed for setting {item['setting']['id']}: {str(e)}")

    results = []
    for item in prediction_ids:
        try:
            import sys
            sys.stdout.write(f"Polling enhancement prediction {item['prediction_id']}...\n")
            sys.stdout.flush()

            final_result = poll_prediction(item['prediction_id'])

            sys.stdout.write(f"Got enhancement result: {final_result}\n")
            sys.stdout.flush()

            output_urls = final_result.get('output') or final_result.get('outputs') or final_result.get('data', {}).get('outputs')

            if output_urls:
                url = output_urls[0] if isinstance(output_urls, list) else output_urls
                results.append({
                    'image_url': url,
                    'setting': item['setting']
                })
                sys.stdout.write(f"Added enhanced image URL: {url}\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"Enhancement polling failed for prediction {item['prediction_id']}: {str(e)}\n")
            sys.stdout.flush()

    return results
