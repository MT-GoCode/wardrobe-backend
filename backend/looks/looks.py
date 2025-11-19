import uuid

looks = {
    # Studio - Woman
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "facing front-left with one foot slightly forward and left arm on hip",
        "setting": "white studio backdrop",
        "lighting": "high-contrast spotlight from upper left",
        "gender": "woman",
        "hair": "straight down with slight lift",
        "expression": "focused neutral"
    },

    # Studio - Man
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "facing slightly left, right hand in pocket, other arm relaxed, leaning on right leg",
        "setting": "white studio backdrop",
        "lighting": "high-contrast spotlight from upper left",
        "gender": "man",
        "hair": "straight down with slight lift",
        "expression": "focused neutral"
    },

    # Urban - Woman
    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "light step forward with one hand lifting hair",
        "setting": "city sidewalk on a brightly lit, blue-sky summer day",
        "lighting": "brown apartment building to the right and street to the left lined with trees",
        "gender": "woman",
        "hair": "wind-blown backward",
        "expression": "soft determination"
    },
    
    # Urban - Man
    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "standing in a relaxed stance with fingers hooked on hips, head slightly cocked to the side, subtle smirk",
        "setting": "city sidewalk on a brightly lit, blue-sky summer day",
        "lighting": "brown apartment building to the right and a tree-lined street to the left",
        "gender": "man",
        "hair": "short and natural",
        "expression": "subtle confident smirk"
    },

    # Beach - Woman
    str(uuid.uuid4().hex): { 
        "type": "Beach",
        "pose": "arms by side, chest out",
        "setting": "on the beach shoreline at sunrise, well-lit and evenly illuminated",
        "lighting": "warm yellow sunlight from the left",
        "gender": "woman",
        "hair": "blowing in the wind",
        "expression": "eyes closed, serene"
    },

    # Beach - Man
    str(uuid.uuid4().hex): {
        "type": "Beach",
        "pose": "standing with a slight turn toward the left, shoulders relaxed, one leg subtly forward, looking at the camera",
        "setting": "on the beach shoreline at sunrise, well-lit and evenly illuminated",
        "lighting": "warm yellow sunlight from the left casting soft highlights across the body",
        "gender": "man",
        "hair": "wind-blown backward",
        "expression": "calm confident gaze toward the camera"
    },

    # Nightclub - Woman 1 (suggest renaming type as Nightclub A)
    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "one arm elevated with gentle torso twist",
        "setting": "modern dim lounge interior",
        "lighting": "deep red tungsten glow with cool side fill",
        "gender": "woman",
        "hair": "straight down",
        "expression": "calm allure"
    },

    # Nightclub - Woman 2 (suggest Nightclub B)
    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "soft step with one hand tracing her jawline",
        "setting": "boutique bar with ambient colored lighting",
        "lighting": "low warm ambient light with crisp teal rim light",
        "gender": "woman",
        "hair": "wind-blown backward",
        "expression": "serious softness"
    },

    # Nature - Woman
    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "standing with arms relaxed, head tilted upward as she gazes dreamily at the sunlit trees",
        "setting": "on a forest nature trail with tall trees lining both sides and the trail extending behind, warm sunlight leaking through the branches from the right side",
        "lighting": "soft warm sunbeams filtering through the trees, highlighting the face and hair",
        "gender": "woman",
        "hair": "loose and lightly wind-blown",
        "expression": "dreamy peaceful wonder"
    },

    # Nature - Man
    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "standing with arms crossed and a slight turn toward the camera, relaxed confident posture",
        "setting": "on a forest nature trail with tall trees lining both sides and the trail extending behind, warm sunlight leaking through the branches from the right side",
        "lighting": "soft warm sunbeams filtering through the trees, highlighting the face and upper body",
        "gender": "man",
        "hair": "short and naturally styled",
        "expression": "calm confident focus"
    },

    # Workplace - Woman
    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "standing with a soft turn toward the camera, one hand lightly holding her forearm, relaxed professional stance",
        "setting": "in a brightly lit white workplace hallway on a high floor with large windows looking out onto nearby skyscrapers",
        "lighting": "clean bright daylight from the windows creating soft natural highlights",
        "gender": "woman",
        "hair": "smooth, slightly wavy, neatly styled",
        "expression": "warm focused professionalism"
    },

    # Workplace - Man
    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "standing with a slight turn toward the camera, one hand in pocket, shoulders relaxed, confident professional stance",
        "setting": "in a brightly lit white workplace hallway on a high floor with large windows looking out onto nearby skyscrapers",
        "lighting": "clean bright daylight from the windows creating soft natural highlights",
        "gender": "man",
        "hair": "short neatly styled",
        "expression": "calm confident focus"
    }
}
