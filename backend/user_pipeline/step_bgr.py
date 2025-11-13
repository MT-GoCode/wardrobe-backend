from ai_api_utils.replicate import run_prediction_sync

MODEL_VERSION = "95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1"

def remove_background(image_url):
    input_payload = {
        "image": image_url
    }

    result = run_prediction_sync(input_payload, model_version=MODEL_VERSION)
    output_url = result.get('output')

    return output_url
