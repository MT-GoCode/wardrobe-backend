import json
from ai_api_utils.openai_api import vision_completion
from db_utils import supabase


def detect_gender(person_image_url):
    """
    Detect if the person in the image is male or female.
    Returns 'male' or 'female'.
    """
    system_prompt = "You are a gender detection assistant. You must respond with ONLY one word: either 'male' or 'female'. No explanation, no punctuation, no additional text."
    prompt = "Look at this person. Is this person male or female? Answer with ONLY one word: 'male' or 'female'."
    
    result = vision_completion(person_image_url, prompt, system_prompt=system_prompt)
    gender = result['choices'][0]['message']['content'].strip().lower()
    
    # Normalize response
    if 'female' in gender or 'woman' in gender:
        return 'female'
    else:
        return 'male'


def analyze_clothing(clothing_image_url):
    """
    Analyze clothing image to get type and style description.
    Returns dict with 'type' and 'style' keys.
    """
    system_prompt = """You are a fashion analysis assistant. You analyze clothing images and return ONLY a JSON object with exactly two keys:
- "type": the type of clothing in 1-3 words (e.g., "skirt", "blazer", "evening dress")
- "style": a brief description of how the garment is worn (e.g., "worn from the waist down and ends at ankles")

Return ONLY the JSON object, no other text, no markdown formatting, no code blocks."""

    prompt = """Analyze this clothing item. Return a JSON object with:
1. "type": the type of clothing in 1-3 words
2. "style": a brief description of how this garment is typically worn

Example response:
{"type": "skirt", "style": "worn from the waist down and ends at ankles"}

Return ONLY the JSON object, nothing else."""

    result = vision_completion(clothing_image_url, prompt, system_prompt=system_prompt, max_tokens=200)
    response_text = result['choices'][0]['message']['content'].strip()
    
    # Try to parse JSON from response
    try:
        # Handle potential markdown code blocks
        if '```' in response_text:
            # Extract JSON from code block
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]
        
        clothing_info = json.loads(response_text)
        return {
            'type': clothing_info.get('type', 'garment'),
            'style': clothing_info.get('style', 'worn on the body')
        }
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            'type': 'garment',
            'style': 'worn on the body'
        }


def build_garment_description(clothing_info):
    """
    Build the full garment description object for the Gemini prompt.
    """
    return {
        "source": "image_2",
        "type": clothing_info['type'],
        "style": clothing_info['style'],
        "preserve_texture": True,
        "preserve_color": True,
        "preserve_length_and_shape": True,
        "simulate_realistic_draping": True
    }


def get_preset_details(preset_ids, is_male):
    """
    Query presets and presets_details tables to get the reference images and descriptions
    for the given preset IDs, filtered by gender.
    
    Args:
        preset_ids: List of preset IDs (integers)
        is_male: Boolean - True if the model is male
        
    Returns:
        List of dicts with 'preset_id', 'name', 'ref_image_full', 'description'
    """
    results = []
    
    # In presets_details: gender = false means male, gender = true means female
    gender_filter = not is_male  # male -> false, female -> true
    
    for preset_id in preset_ids:
        # Query presets_details filtered by preset_id and gender
        response = supabase.table('presets_details').select(
            'id, ref_image_full, description, presets(id, name)'
        ).eq('id', preset_id).eq('gender', gender_filter).execute()
        
        if response.data and len(response.data) > 0:
            detail = response.data[0]
            results.append({
                'preset_id': preset_id,
                'name': detail.get('presets', {}).get('name', ''),
                'ref_image_full': detail.get('ref_image_full', ''),
                'description': detail.get('description', '')
            })
    
    return results


def analyze(person_image_url, clothing_image_url, preset_ids):
    """
    Analyze step of the inference pipeline.
    
    1. Detect gender from person image
    2. Analyze clothing to get type and style
    3. Build garment description
    4. Query preset details based on gender
    
    Args:
        person_image_url: URL of the person/model image
        clothing_image_url: URL of the clothing image
        preset_ids: List of preset IDs (integers)
        
    Returns:
        Dict with analysis results including garment_description and preset_details
    """
    # Step 1: Detect gender
    gender = detect_gender(person_image_url)
    is_male = (gender == 'male')
    
    # Step 2: Analyze clothing
    clothing_info = analyze_clothing(clothing_image_url)
    
    # Step 3: Build garment description
    garment_description = build_garment_description(clothing_info)
    
    # Step 4: Get preset details filtered by gender
    preset_details = get_preset_details(preset_ids, is_male)
    
    return {
        'gender': gender,
        'clothing_type': clothing_info['type'],
        'clothing_style': clothing_info['style'],
        'garment_description': garment_description,
        'preset_details': preset_details
    }
