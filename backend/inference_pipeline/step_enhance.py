import os
import json
import tempfile
import requests
from io import BytesIO
from PIL import Image as PILImage
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .prompts import get_enhance_prompt

load_dotenv()


def download_image_to_pil(url):
    """
    Download an image from URL and return as PIL Image object.
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return PILImage.open(BytesIO(response.content))


def enhance_image(image_url, clothing_type, max_retries=3):
    """
    Enhance an image using Gemini's image generation to harmonize the clothing.
    
    Uses the same SDK pattern as generate:
    - Download image and open with PIL Image.open()
    - Pass image and prompt to generate_content
    - Handle response parts properly
    - Retries up to max_retries times if response is None or has no parts
    
    Args:
        image_url: URL of the generated image to enhance
        clothing_type: String describing the clothing type (e.g., "skirt", "dress")
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        bytes: The enhanced image data, or None if all retries fail
    """
    api_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_STUDIO_API_KEY not found in environment")
    
    # Build the enhance prompt
    prompt_text = get_enhance_prompt(clothing_type)
    
    # Download image and open with PIL
    image = download_image_to_pil(image_url)
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Retry logic
    for attempt in range(max_retries):
        try:
            # Use the same pattern as generate - prompt first, then image
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[
                    prompt_text,
                    image,
                ],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",
                        image_size="4K"
                    ),
                )
            )
            
            # Check if response or response.parts is None
            if response is None or response.parts is None:
                if attempt < max_retries - 1:
                    continue  # Retry
                else:
                    return None  # All retries exhausted
            
            # Extract the generated image from response
            enhanced_image = None
            for part in response.parts:
                if part.text is not None:
                    # Text response (if any)
                    continue
                elif image := part.as_image():
                    enhanced_image = image
                    break
            
            if not enhanced_image:
                if attempt < max_retries - 1:
                    continue  # Retry
                else:
                    return None  # All retries exhausted
            
            # part.as_image() returns a google.genai.types.Image object
            # Its save() method only accepts a file path (string), not a file-like object
            # So we save to a temporary file and read it back
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            enhanced_image.save(tmp_path)
            
            # Read the file back as bytes
            with open(tmp_path, 'rb') as f:
                image_bytes = f.read()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return image_bytes
            
        except Exception as e:
            # If this is the last attempt, return None
            if attempt < max_retries - 1:
                continue  # Retry on exception
            else:
                # Log the error but return None gracefully
                return None
    
    # Should not reach here, but return None as fallback
    return None


def enhance(generated_image_url, clothing_type):
    """
    Main enhance function for a single generated image.
    
    Args:
        generated_image_url: URL of the generated image from step_generate
        clothing_type: String describing the clothing type from step_analyze
        
    Returns:
        bytes: The enhanced image data, or None if enhancement fails after retries
    """
    return enhance_image(
        image_url=generated_image_url,
        clothing_type=clothing_type
    )

