import os
from ai_api_utils.replicate import run_prediction_sync
from dotenv import load_dotenv

load_dotenv()

GPT4O_MINI_VERSION = "2c0a6a34916017ceafaaf5fdf63f9370cf9491866a9611f37d86138c8ef53fc6"


def vision_completion(image_url, prompt, system_prompt=None, max_tokens=500):
    input_payload = {
        "prompt": prompt,
        "image_input": [image_url],
        "max_tokens": max_tokens,
        "temperature": 0
    }

    if system_prompt:
        input_payload["system_prompt"] = system_prompt

    result = run_prediction_sync(input_payload, model_version=GPT4O_MINI_VERSION)
    output_text = "".join(result.get('output', []))

    return {
        'choices': [{
            'message': {
                'content': output_text
            }
        }]
    }


def multi_image_completion(image_urls, prompt, system_prompt=None, max_tokens=1000):
    input_payload = {
        "prompt": prompt,
        "image_input": image_urls,
        "max_tokens": max_tokens,
        "temperature": 0
    }

    if system_prompt:
        input_payload["system_prompt"] = system_prompt

    result = run_prediction_sync(input_payload, model_version=GPT4O_MINI_VERSION)
    output_text = "".join(result.get('output', []))

    return {
        'choices': [{
            'message': {
                'content': output_text
            }
        }]
    }
