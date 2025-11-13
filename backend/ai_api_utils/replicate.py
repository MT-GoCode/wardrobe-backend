import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
REPLICATE_BASE_URL = 'https://api.replicate.com/v1'


def create_prediction(input_payload, model_version=None):
    """
    Generic POST request to create a Replicate prediction.

    Args:
        input_payload: dict containing the input parameters for the model
        model_version: Optional specific model version string

    Returns:
        dict: Response from Replicate API containing prediction ID and initial status
    """
    url = f"{REPLICATE_BASE_URL}/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"input": input_payload}
    if model_version:
        payload["version"] = model_version

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create Replicate prediction: {str(e)}")


def get_prediction(prediction_id):
    """
    Generic GET request to retrieve a Replicate prediction result.

    Args:
        prediction_id: str, the unique prediction ID returned from create_prediction

    Returns:
        dict: Response from Replicate API containing prediction status and output
    """
    url = f"{REPLICATE_BASE_URL}/predictions/{prediction_id}"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get Replicate prediction: {str(e)}")


def poll_prediction(prediction_id, max_wait_seconds=300, poll_interval=2):
    """
    Poll a Replicate prediction until completion or timeout.

    Args:
        prediction_id: str, the unique prediction ID
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 2)

    Returns:
        dict: Final prediction result with status 'succeeded' or 'failed'

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        result = get_prediction(prediction_id)
        status = result.get('status')

        if status == 'succeeded':
            return result
        elif status == 'failed':
            error_msg = result.get('error', 'Unknown error')
            raise Exception(f"Replicate prediction failed: {error_msg}")
        elif status in ['starting', 'processing']:
            time.sleep(poll_interval)
        else:
            time.sleep(poll_interval)

    raise Exception(f"Replicate prediction timed out after {max_wait_seconds} seconds")


def cancel_prediction(prediction_id):
    """
    Cancel a running Replicate prediction.

    Args:
        prediction_id: str, the unique prediction ID

    Returns:
        dict: Response from Replicate API
    """
    url = f"{REPLICATE_BASE_URL}/predictions/{prediction_id}/cancel"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to cancel Replicate prediction: {str(e)}")


def run_prediction_sync(input_payload, model_version=None, max_wait_seconds=300, poll_interval=2):
    """
    Convenience function to create and poll a prediction synchronously.

    Args:
        input_payload: dict containing the input parameters for the model
        model_version: Optional specific model version string
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 2)

    Returns:
        dict: Final prediction result with output

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    # Create prediction
    creation_result = create_prediction(input_payload, model_version)
    prediction_id = creation_result.get('id')

    if not prediction_id:
        raise Exception("Failed to get prediction ID from Replicate response")

    # Poll until completion
    final_result = poll_prediction(prediction_id, max_wait_seconds, poll_interval)

    return final_result
