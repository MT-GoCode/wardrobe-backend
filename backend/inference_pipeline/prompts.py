"""
Prompt templates for the inference pipeline.
"""

GENERATE_PROMPT = """{
  "task": "two_stage_vton_then_subject_replacement",

  THE FINAL OUTPUT MUST HAVE THE PERSON FROM IMAGE_1, AND NONE OF THE PERSON FROM IMAGE_3. THE IDENTITY MUST COME FROM IMAGE_1 ALONE.

  "mode": "multi_image_fusion",

  "image_roles": {
    "image_1": "model_identity_source",
    "image_2": "garment_source",
    "image_3": "scene_and_pose_reference"
  },

  "stage_1_VTON": {
    "goal": "Apply the garment from image_2 onto the person from image_1. The appropriate garments from image_1 should be replaced by this new garment. Disregard the backgrounds from image_1 and image_2 completely.",

    "identity": {
      "source": "image_1",
      "preserve_face": true,
      "preserve_eyes": true,
      "preserve_hair": true,
      "preserve_hair_color": true,
      "preserve_hairline": true,
      "preserve_skin_color": true,
      "preserve_eyes": true,
      "preserve_hairstyle": true, such as bangs, long hair, curly hair, ponytails etc.,
      "preserve_skin_tone": true,
      "preserve_body_shape": true,
      "identity_strength": 1.0,
    },

    "garment": <<<GARMENT_DESCRIPTION>>>

  },

  "stage_2_subject_replacement": {
    "goal": "Replace the subject in image_3 with the output from Stage 1",

    "identity_strength_of_image_3": 0.0,

    "background_lock": {
      "source": "image_3",
      "preserve_every_pixel_outside_original_subject": true,
      "no_scene_regeneration": true,
      "no_new_objects": true,
      "allowed_modification_zone": "original_subject_silhouette_only"
    },

    "image_3_description": <<<REF_IMG_DESCRIPTION>>>,


    "pose_and_expression_policy": {
      "match_image_3_exactly": true
    },

    "placement_and_geometry": {
      "match_original_subject_position": true,
      "match_original_subject_scale": true,
      "match_camera_angle": true,
      "match_ground_plane": true,
      "match_horizon_line": true
    },

    "relighting": {
      "source": "image_3",
      "dominant_color": "blue",
      "match_shadow_direction": true,
      "match_shadow_intensity": true,
      "match_shadow_softness": true,
      "preserve_environment_lighting": true
    },

    "rendering": {
      "style": "photorealistic",
      "seamless_integration": true,
      "no_cutout_edges": true,
      "no_halos": true
    }
  },

  "negative_prompt": [
    "using_body_parts_from_image_3",
    "misproportioned limbs",
    "wrong body proporitons",
    "change background",
    "change lighting in background",
    "change pose",
    "change expression",
    "wrong subject scale",
    "wrong camera angle",
    "identity change",
    "hair change",
    "bad anatomy",
    "cutout effect",
    "halo",
    "floating subject",
    "wrong color cast",
    "wrong shadows",
    "background blur"
  ],

  "output": {
    "background": "image_3_exact",
    "resolution": "image_3_exact_square",
    "format": "png",
    "quality": "maximum"
  }
}"""


def get_enhance_prompt(clothing_type):
    """
    Get the enhance prompt with clothing type filled in.
    
    Args:
        clothing_type: String describing the clothing type (e.g., "skirt", "dress")
        
    Returns:
        String prompt for enhancement
    """
    return f"""Harmonize and correct the {clothing_type} so it appears naturally integrated into the original outdoor scene.

Instructions:

Do NOT change the subject's pose, body shape, face, expression, or background. Do NOT change the garment design or pattern. Only modify the lighting, texture, edges, shadows, and color blending of the {clothing_type} so it appears physically present in the scene.

In addition, enhance or sharpen the quality of the image so it's as if this photo was taken by a professional camera, without hallucinating any new details.
"""

