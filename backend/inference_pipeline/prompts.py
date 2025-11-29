"""
Prompt templates for the inference pipeline.
"""

GENERATE_PROMPT = """{
  THE OUTPUT OF THIS IMAGE IS MEANT TO BE USED FOR PROFESSIONAL FASHION PURPOSES AND SHOWN TO PUBLIC, WITH NO INTENTION OF SEXUAL OR PROVOCATIVE IMAGERY.

  "task": "two_stage_vton_then_subject_replacement",

  "mode": "multi_image_fusion",

  "image_roles": {
    "image_1": "model_identity_source",
    "image_2": "garment_source",
    "image_3": "scene_and_pose_reference (mannequin_only)"
  },

  "note": "IMAGE_3 CONTAINS A MANNEQUIN, NOT A REAL PERSON. DO NOT USE ANY IDENTITY TRAITS FROM IMAGE_3. THE FINAL OUTPUT MUST HAVE THE PERSON FROM IMAGE_1 ONLY.",
  

  "stage_1_VTON": {
    "goal": "Apply the garment from image_2 onto the person from image_1. Replace only the relevant clothing. Ignore all backgrounds from image_1 and image_2.",

    "identity": {
      "source": "image_1",
      "preserve_face": true,
      "preserve_eyes": true,
      "preserve_hair": true,
      "preserve_hair_color": true,
      "preserve_hairline": true,
      "preserve_hairstyle": true,
      "preserve_skin_color": true,
      "preserve_skin_tone": true,
      "preserve_body_shape": true,
      "identity_strength": 1.0
    },

    "garment": <<<GARMENT_DESCRIPTION>>>
  },

  "stage_2_subject_replacement": {
    "goal": "Replace the mannequin in image_3 with the Stage 1 output. The mannequin is only used for pose, placement, and lighting reference.",

    "identity_strength_of_image_3": 0.0,

    "note": "Do not generic generic model face on the mannequin use the model's face exactly instead of trying to beautify it or hallucinating a new face or any details."
    "note": "If the input garment are feetwear, make sure they appear, otherwise please generate small shoes or barefoot based on appropriateness of setting"

    "background_lock": {
      "source": "image_3",
      "preserve_every_pixel_outside_original_subject": true,
      "no_scene_regeneration": true,
      "no_new_objects": true,
      "allowed_modification_zone": "original_mannequin_silhouette_only"
    },

    "image_3_description": <<<REF_IMG_DESCRIPTION>>>,

    "pose_and_expression_policy": {
      "match_image_3_exactly": true,
      "note": "Match the mannequin's pose only. Do not copy any mannequin identity, features, or body proportions."
      "note": "Assume the mannequin is of average height, and make the person's height the same, more, or less than mannequin as appropriate, but if the person seems of average height, make them the same height as the mannequin."
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
      "match_environment_lighting": true,
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
    "copying_mannequin_features",
    "mannequin_identity_transfer",
    "wrong body proportions",
    "misproportioned limbs",
    "changing background",
    "changing lighting in background",
    "changing pose",
    "changing expression",
    "changing subject scale",
    "wrong camera angle",
    "identity change",
    "hair change",
    "bad anatomy",
    "cutout edges",
    "halo",
    "floating subject",
    "incorrect color cast",
    "incorrect shadows",
    "background blur"
  ],

  "output": {
    "background": "image_3_exact",
    "resolution": "image_3_exact_square",
    "format": "png",
    "quality": "maximum"
  }
}
"""


def get_enhance_prompt(clothing_type):
    """
    Get the enhance prompt with clothing type filled in.
    
    Args:
        clothing_type: String describing the clothing type (e.g., "skirt", "dress")
        
    Returns:
        String prompt for enhancement
    """
    return f"""{{
  
  "no_cut_and_paste": This image is fundamentally a combination of many, so it may appear photoshopped or as if naively pasted together. Reduce the appearance of cut-and-paste as much as possible, such as on the {clothing_type} or the entire subject. Everything must blend seamlessly.  "enhance_texture": "Refine the {clothing_type} texture and surface detail so it looks realistic, including natural fabric grain, micro-wrinkles, and proper light response.",
  "film_grain": "Add film grain to the image, especially on the subject, to make everything blend better and make it more realistic and cinematic.",
  "realistic_skin": "Have realistic skin textures that aren't too smooth and have shading consistent with the scene's lighting.",
  "check_face_and_eyes": "Ensure the face and eyes are not distorted and have realistic textures",
  "improve_lighting_match": "Adjust the {clothing_type}'s lighting so it matches the ambient light direction, color, and intensity of the scene.",
  "blend_edges": "Blend and correct {clothing_type} edges so they sit naturally against the body with clean transitions and no cutout artifacts.",
  "fix_shadows": "Ensure {clothing_type} shadows match the scene's lighting, including direction, softness, and depth.",
  "color_harmonization": "Match {clothing_type} color and tonal balance to the scene so it looks physically present, without shifting the original design.",
  "correct_artifacts": "Fix any distortions, flattening, or unrealistic overlaps between {clothing_type} and skin.",
  "overall_quality_enhancement": "Enhance clarity of the subject to match that of the scene, without adding new objects or altering the environment.",

  "negative": "Do not hallucinate new details. Do not change background, identity, pose, body proportions, hairstyle, environment lighting, or add accessories."
}}"""


