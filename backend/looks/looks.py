import uuid

looks = {
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "slight contrapposto with one hand lifting hair",
        "setting": "matte grey studio backdrop",
        "lighting": "high-contrast spotlight from upper left",
        "gender": "woman",
        "hair": "straight down with slight lift",
        "expression": "focused neutral"
    },
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "one arm raised with elbow angled",
        "setting": "soft beige gradient studio wall",
        "lighting": "soft diffused top light",
        "gender": "woman",
        "hair": "slicked back",
        "expression": "calm intensity"
    },
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "gentle lean with hand touching neck",
        "setting": "minimal white cyclorama",
        "lighting": "clean beauty light from front",
        "gender": "woman",
        "hair": "straight down",
        "expression": "soft neutral"
    },

    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "light step forward with hand lifting hair",
        "setting": "concrete rooftop",
        "lighting": "late-morning crisp sunlight",
        "gender": "woman",
        "hair": "wind backward",
        "expression": "soft determination"
    },
    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "arm bent overhead",
        "setting": "minimal city alley wall",
        "lighting": "sun slicing across face",
        "gender": "woman",
        "hair": "straight down",
        "expression": "neutral power"
    },

    str(uuid.uuid4().hex): {
        "type": "Beach",
        "pose": "one arm lifted with elbow bent",
        "setting": "sunset shoreline",
        "lighting": "warm backlight reflecting off ocean",
        "gender": "woman",
        "hair": "wind backward",
        "expression": "peaceful intensity"
    },
    str(uuid.uuid4().hex): {
        "type": "Beach",
        "pose": "gentle lean with hand brushing hairline",
        "setting": "coastal rocks",
        "lighting": "harsh sun from above",
        "gender": "woman",
        "hair": "straight down",
        "expression": "soft focus"
    },

    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "one arm elevated with gentle torso twist",
        "setting": "dim lounge",
        "lighting": "deep red tungsten with cool side fill",
        "gender": "woman",
        "hair": "straight down",
        "expression": "calm allure"
    },
    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "soft step with hand tracing jawline",
        "setting": "boutique bar",
        "lighting": "low warm lighting with crisp teal rim",
        "gender": "woman",
        "hair": "breeze backward",
        "expression": "serious softness"
    },

    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "gentle turn with arm bent across torso",
        "setting": "forest path",
        "lighting": "sunshaft beam illuminating upper face",
        "gender": "woman",
        "hair": "wind backward",
        "expression": "soft serenity"
    },
    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "weight on one leg with hand lifting hair",
        "setting": "tall grass meadow",
        "lighting": "golden hour halo lighting",
        "gender": "woman",
        "hair": "wind to the side",
        "expression": "peaceful"
    },

    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "shoulders angled with hand on upper arm",
        "setting": "minimal beige wall",
        "lighting": "soft editorial key light",
        "gender": "woman",
        "hair": "no change",
        "expression": "calm determination"
    },
    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "torso angled with arm lifting behind head",
        "setting": "modern office exterior",
        "lighting": "bright but soft overcast light",
        "gender": "woman",
        "hair": "no change",
        "expression": "quiet neutral"
    },

    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "slight lean with hand at chest",
        "setting": "concrete-grey backdrop",
        "lighting": "hard overhead key",
        "gender": "man",
        "hair": "no change",
        "expression": "focused"
    },
    str(uuid.uuid4().hex): {
        "type": "Studio",
        "pose": "one hand near chin",
        "setting": "black studio void",
        "lighting": "sharp facial side slice",
        "gender": "man",
        "hair": "no change",
        "expression": "controlled intensity"
    },

    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "one hand behind neck with soft lean",
        "setting": "sunlit concrete wall",
        "lighting": "strong high sun",
        "gender": "man",
        "hair": "no change",
        "expression": "subtle intensity"
    },
    str(uuid.uuid4().hex): {
        "type": "Urban",
        "pose": "light torso rotation",
        "setting": "overpass walkway",
        "lighting": "cool skylight",
        "gender": "man",
        "hair": "slicked back",
        "expression": "focused calm"
    },

    str(uuid.uuid4().hex): {
        "type": "Beach",
        "pose": "stepping through shallow water",
        "setting": "shoreline reflection",
        "lighting": "bright reflective sun",
        "gender": "man",
        "hair": "wind pushed back",
        "expression": "neutral intensity"
    },
    str(uuid.uuid4().hex): {
        "type": "Beach",
        "pose": "torso angled with arm raised outward",
        "setting": "coastal rocks",
        "lighting": "crisp cool daylight",
        "gender": "man",
        "hair": "slicked back",
        "expression": "focused calm"
    },

    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "arm diagonally lifted across torso",
        "setting": "club hallway",
        "lighting": "deep tungsten with magenta rim",
        "gender": "man",
        "hair": "slicked back",
        "expression": "calm intensity"
    },
    str(uuid.uuid4().hex): {
        "type": "Nightclub",
        "pose": "slight forward lean with hand at jaw",
        "setting": "bar counter backdrop",
        "lighting": "warm amber and cold teal cross-lighting",
        "gender": "man",
        "hair": "no change",
        "expression": "moody focus"
    },

    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "slight backward lean with hand behind head",
        "setting": "forest edge",
        "lighting": "soft skylight with warm glow",
        "gender": "man",
        "hair": "wind backward",
        "expression": "calm neutral"
    },
    str(uuid.uuid4().hex): {
        "type": "Nature",
        "pose": "light step with arm bent across abdomen",
        "setting": "mountain overlook",
        "lighting": "cool morning atmosphere",
        "gender": "man",
        "hair": "no change",
        "expression": "quiet focus"
    },

    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "torso twist with hand at jawline",
        "setting": "charcoal-grey backdrop",
        "lighting": "angled spotlight",
        "gender": "man",
        "hair": "slicked back",
        "expression": "measured confidence"
    },
    str(uuid.uuid4().hex): {
        "type": "Workplace",
        "pose": "gentle forward lean with arm lifted diagonally",
        "setting": "slate-blue photo backdrop",
        "lighting": "cool top-down illumination",
        "gender": "man",
        "hair": "slicked back",
        "expression": "focused neutrality"
    }
}
