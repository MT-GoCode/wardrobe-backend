from ai_api_utils.openai_api import vision_completion, multi_image_completion
from looks.looks import looks
import random


def detect_gender(person_image_url):
    system_prompt = "You are a gender detection assistant. You must respond with ONLY one word: 'man' or 'woman'. No explanation, no punctuation, no additional text."
    prompt = "Look at this person. Answer with ONLY one word: 'man' or 'woman'."
    result = vision_completion(person_image_url, prompt, system_prompt=system_prompt)
    gender = result['choices'][0]['message']['content'].strip().lower()
    return gender


def detect_clothing_type(clothing_image_urls):
    system_prompt = "You are a fashion assistant that analyzes clothing. You must respond with ONLY one word."
    prompt = """Analyze the clothing in these images. Describe the clothing type in ONE WORD (examples: dress, suit, shirt, pants, jacket, skirt, blouse, coat).

Respond with ONLY that one word, nothing else."""
    result = multi_image_completion(clothing_image_urls, prompt, system_prompt=system_prompt)
    clothing_type = result['choices'][0]['message']['content'].strip().lower()
    return clothing_type


def select_random_look(gender, setting_type):
    filtered = {k: v for k, v in looks.items() if v['gender'] == gender and v['type'] == setting_type}
    if not filtered:
        return None
    selected_id = random.choice(list(filtered.keys()))
    return {'id': selected_id, **filtered[selected_id]}


def analyze(person_image_url, clothing_image_urls, setting_types):
    gender = detect_gender(person_image_url)
    clothing_type = detect_clothing_type(clothing_image_urls)

    settings = []
    for st in setting_types:
        look = select_random_look(gender, st)
        if look:
            settings.append(look)

    return {
        'gender': gender,
        'clothing_type': clothing_type,
        'settings': settings
    }
