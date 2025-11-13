import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

FAL_API_KEY = os.getenv('FAL_API_KEY')
FAL_BASE_URL = 'https://fal.run'


def create_prediction(model_path, input_payload):
    """
    Generic POST request to create a Fal AI prediction.

    Args:
        model_path: str, the model path (e.g., 'fal-ai/iclight-v2')
        input_payload: dict containing the input parameters for the model

    Returns:
        dict: Response from Fal AI API containing request_id for polling
    """
    url = f"{FAL_BASE_URL}/{model_path}"
    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=input_payload, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create Fal AI prediction: {str(e)}")


def get_prediction_status(model_path, request_id):
    """
    Generic GET request to retrieve a Fal AI prediction status.

    Args:
        model_path: str, the model path (e.g., 'fal-ai/iclight-v2')
        request_id: str, the unique request ID

    Returns:
        dict: Response from Fal AI API containing status and possibly result
    """
    url = f"{FAL_BASE_URL}/{model_path}/requests/{request_id}/status"
    headers = {
        "Authorization": f"Key {FAL_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get Fal AI prediction status: {str(e)}")


def get_prediction_result(model_path, request_id):
    """
    Generic GET request to retrieve a Fal AI prediction result.

    Args:
        model_path: str, the model path (e.g., 'fal-ai/iclight-v2')
        request_id: str, the unique request ID

    Returns:
        dict: Response from Fal AI API containing the final result
    """
    url = f"{FAL_BASE_URL}/{model_path}/requests/{request_id}"
    headers = {
        "Authorization": f"Key {FAL_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=600)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get Fal AI prediction result: {str(e)}")


def poll_prediction(model_path, request_id, max_wait_seconds=300, poll_interval=2):
    """
    Poll a Fal AI prediction until completion or timeout.

    Args:
        model_path: str, the model path (e.g., 'fal-ai/iclight-v2')
        request_id: str, the unique request ID
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 2)

    Returns:
        dict: Final prediction result

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        status_result = get_prediction_status(model_path, request_id)
        status = status_result.get('status')

        if status == 'COMPLETED':
            # Get full result
            return get_prediction_result(model_path, request_id)
        elif status == 'FAILED':
            error_msg = status_result.get('error', 'Unknown error')
            raise Exception(f"Fal AI prediction failed: {error_msg}")
        elif status in ['IN_PROGRESS', 'IN_QUEUE']:
            time.sleep(poll_interval)
        else:
            time.sleep(poll_interval)

    raise Exception(f"Fal AI prediction timed out after {max_wait_seconds} seconds")


def run_prediction_sync(model_path, input_payload, max_wait_seconds=300, poll_interval=2):
    """
    Convenience function to create and poll a prediction synchronously.

    Args:
        model_path: str, the model path (e.g., 'fal-ai/iclight-v2')
        input_payload: dict containing the input parameters for the model
        max_wait_seconds: int, maximum time to wait for completion (default: 300)
        poll_interval: int, seconds between polling attempts (default: 2)

    Returns:
        dict: Final prediction result with output

    Raises:
        Exception: If prediction fails or timeout is reached
    """
    # Create prediction
    creation_result = create_prediction(model_path, input_payload)
    request_id = creation_result.get('request_id')

    if not request_id:
        raise Exception("Failed to get request ID from Fal AI response")

    # Poll until completion
    final_result = poll_prediction(model_path, request_id, max_wait_seconds, poll_interval)

    return final_result
