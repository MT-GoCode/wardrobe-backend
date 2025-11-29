import os
import json
import tempfile
import requests
from io import BytesIO
from PIL import Image as PILImage
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .prompts import GENERATE_PROMPT

load_dotenv()


def build_prompt(garment_description, ref_img_description):
    """
    Build the full prompt by replacing placeholders in the template.
    
    Args:
        garment_description: Dict with garment info (will be JSON stringified)
        ref_img_description: String description of the reference image
    """
    template = GENERATE_PROMPT
    
    # Convert garment_description to JSON string
    garment_json = json.dumps(garment_description, indent=6)
    
    # Wrap ref_img_description in quotes for JSON
    ref_desc_json = json.dumps(ref_img_description)
    
    # Replace placeholders
    prompt = template.replace('<<<GARMENT_DESCRIPTION>>>', garment_json)
    prompt = prompt.replace('<<<REF_IMG_DESCRIPTION>>>', ref_desc_json)
    
    return prompt


def download_image_to_pil(url):
    """
    Download an image from URL and return as PIL Image object.
    This is what Image.open() expects - a file-like object or path.
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return PILImage.open(BytesIO(response.content))


def generate_image(model_image_url, clothing_image_url, ref_image_url, garment_description, ref_img_description, max_retries=3):
    """
    Generate an image using Gemini's image generation SDK.
    
    Uses the exact pattern from gemini_guide.txt:
    - Download images and open with PIL Image.open()
    - Pass images directly to generate_content
    - Handle response parts properly
    - Retries up to max_retries times if response is None or has no parts
    
    Args:
        model_image_url: URL of the model/person image (image_1)
        clothing_image_url: URL of the clothing image (image_2)
        ref_image_url: URL of the reference/scene image (image_3)
        garment_description: Dict with garment description
        ref_img_description: String description of the reference image
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        bytes: The generated image data, or None if all retries fail
    """
    api_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_STUDIO_API_KEY not found in environment")
    
    # Build the prompt
    prompt_text = build_prompt(garment_description, ref_img_description)
    
    # Download images and open with PIL (as shown in gemini_guide.txt)
    model_image = download_image_to_pil(model_image_url)
    clothing_image = download_image_to_pil(clothing_image_url)
    ref_image = download_image_to_pil(ref_image_url)
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Retry logic
    for attempt in range(max_retries):
        try:
            # Use the exact pattern from gemini_guide.txt
            # Order: prompt text, then images in order (image_1, image_2, image_3)
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[
                    prompt_text,
                    model_image,      # image_1
                    clothing_image,   # image_2
                    ref_image,        # image_3
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
            
            # Extract the generated image from response (as shown in gemini_guide.txt)
            generated_image = None
            for part in response.parts:
                if part.text is not None:
                    # Text response (if any)
                    continue
                elif image := part.as_image():
                    generated_image = image
                    break
            
            if not generated_image:
                if attempt < max_retries - 1:
                    continue  # Retry
                else:
                    return None  # All retries exhausted
            
            # part.as_image() returns a google.genai.types.Image object
            # Its save() method only accepts a file path (string), not a file-like object
            # So we save to a temporary file and read it back
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            generated_image.save(tmp_path)
            
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


def generate(model_image_url, clothing_image_url, preset_detail, garment_description):
    """
    Main generate function for a single preset.
    
    Args:
        model_image_url: URL of the model/person image
        clothing_image_url: URL of the clothing image
        preset_detail: Dict with 'ref_image_full' and 'description' keys
        garment_description: Dict with garment description
        
    Returns:
        bytes: The generated image data, or None if generation fails after retries
    """
    ref_image_url = preset_detail['ref_image_full']
    ref_img_description = preset_detail['description']
    
    return generate_image(
        model_image_url=model_image_url,
        clothing_image_url=clothing_image_url,
        ref_image_url=ref_image_url,
        garment_description=garment_description,
        ref_img_description=ref_img_description
    )
