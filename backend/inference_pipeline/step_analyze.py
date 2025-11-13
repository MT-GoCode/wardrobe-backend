from ai_api_utils.openai_api import vision_completion, multi_image_completion
from looks.looks import looks


def detect_gender(person_image_url):
    system_prompt = "You are a gender detection assistant. You must respond with ONLY one word: 'man' or 'woman'. No explanation, no punctuation, no additional text."
    prompt = "Look at this person. Answer with ONLY one word: 'man' or 'woman'."

    result = vision_completion(person_image_url, prompt, system_prompt=system_prompt)
    gender = result['choices'][0]['message']['content'].strip().lower()

    return gender


def select_looks(clothing_image_urls, gender):
    filtered_looks = {k: v for k, v in looks.items() if v['gender'] == gender}

    if not filtered_looks:
        return []

    looks_description = "\n".join([f"ID: {k}\nSetting: {v['setting']}\nLighting: {v['lighting']}\nPose: {v['pose']}\n" for k, v in filtered_looks.items()])

    system_prompt = "You are a fashion assistant that analyzes clothing and selects appropriate settings. You must respond in a specific format with no additional text."

    prompt = f"""Analyze the clothing in these images. First, describe the clothing type in ONE WORD (examples: dress, suit, shirt, pants, jacket).

Then, from the list below, select exactly THREE setting IDs that would best showcase this clothing on a model.

Available settings (filtered for {gender}):
{looks_description}

Respond ONLY in this exact format:
<clothing_type>
<id1>
<id2>
<id3>

Example response:
dress
a1b2c3d4
e5f6g7h8
i9j0k1l2"""

    result = multi_image_completion(clothing_image_urls, prompt, system_prompt=system_prompt)
    response_text = result['choices'][0]['message']['content'].strip()

    lines = [line.strip() for line in response_text.split('\n') if line.strip()]

    if len(lines) < 4:
        raise Exception("Invalid response format from GPT")

    clothing_type = lines[0]
    selected_ids = lines[1:4]

    selected_settings = []
    for selected_id in selected_ids:
        if selected_id in filtered_looks:
            selected_settings.append({
                'id': selected_id,
                **filtered_looks[selected_id]
            })

    return {
        'clothing_type': clothing_type,
        'settings': selected_settings
    }


def analyze(person_image_url, clothing_image_urls):
    gender = detect_gender(person_image_url)
    result = select_looks(clothing_image_urls, gender)

    return {
        'gender': gender,
        'clothing_type': result['clothing_type'],
        'settings': result['settings']
    }
