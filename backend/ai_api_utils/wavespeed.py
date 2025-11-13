import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

WAVESPEED_API_KEY = os.getenv('WAVESPEED_API_KEY')
WAVESPEED_BASE_URL = 'https://api.wavespeed.ai/api/v3'


def create_prediction(model_path, input_payload):
    """
    Generic POST request to create a Wavespeed prediction.

    Args:
        model_path: str, the model path (e.g., 'bytedance/seedream-v4/edit')
        input_payload: dict containing the input parameters for the model

    Returns:
        dict: Response from Wavespeed API containing prediction ID and initial status
    """
    url = f"{WAVESPEED_BASE_URL}/{model_path}"
    headers = {
        "Authorization": f"Bearer {WAVESPEED_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=input_payload, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create Wavespeed prediction: {str(e)}")


def get_prediction(prediction_id):
    """
    Generic GET request to retrieve a Wavespeed prediction result.

    Args:
        prediction_id: str, the unique prediction/request ID

    Returns:
        dict: Response from Wavespeed API containing prediction status and output
    """
    url = f"{WAVESPEED_BASE_URL}/predictions/{prediction_id}/result"
    headers = {
        "Authorization": f"Bearer {WAVESPEED_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get Wavespeed prediction: {str(e)}")


def poll_prediction(prediction_id, max_wait_seconds=300, poll_interval=5):
    """
    Poll a Wavespeed prediction until completion or timeout.

    Args:
        prediction_id: str, the unique prediction ID
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 5)

    Returns:
        dict: Final prediction result with outputs

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        result = get_prediction(prediction_id)

        status = result.get('status') or result.get('data', {}).get('status')
        output = result.get('output') or result.get('data', {}).get('outputs')

        if (status == 'succeeded' or status == 'completed') and output:
            return result
        elif status == 'failed':
            error_msg = result.get('error', 'Unknown error')
            raise Exception(f"Wavespeed prediction failed: {error_msg}")

        time.sleep(poll_interval)

    raise Exception(f"Wavespeed prediction timed out after {max_wait_seconds} seconds")


def run_prediction_sync(model_path, input_payload, max_wait_seconds=300, poll_interval=5):
    """
    Convenience function to create and poll a prediction synchronously.

    Args:
        model_path: str, the model path (e.g., 'bytedance/seedream-v4/edit')
        input_payload: dict containing the input parameters for the model
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 5)

    Returns:
        dict: Final prediction result with output

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    creation_result = create_prediction(model_path, input_payload)
    prediction_id = creation_result.get('id') or creation_result.get('data', {}).get('id')

    if not prediction_id:
        raise Exception("Failed to get prediction ID from Wavespeed response")

    if creation_result.get('status') == 'completed' or creation_result.get('data', {}).get('status') == 'completed':
        return creation_result

    final_result = poll_prediction(prediction_id, max_wait_seconds, poll_interval)

    return final_result
