from .step_analyze import analyze
from .step_generate import generate
from .step_enhance import enhance
from models.image import Image
from db_utils import upload_image_to_supabase
from general_utils import generate_uuid_filename


def run(person_image, clothing_image, preset_ids, run_id=None, progress_callback=None):
    """
    Run the inference pipeline with optional progress tracking.
    
    Three stages:
    1. Analyze (0% -> 25%): Detect gender, analyze clothing, fetch preset details
    2. Generate (25% -> 75%): Generate images for each preset using Gemini
    3. Enhance (75% -> 100%): Enhance each generated image to harmonize clothing
    
    Args:
        person_image: Image object for the person/model
        clothing_image: Image object for the clothing
        preset_ids: List of preset IDs (integers)
        run_id: Optional run ID for progress tracking
        progress_callback: Optional callback function(run_id, progress) to update progress
        
    Returns:
        Dict with analysis, intermediate_outputs, and outputs
    """
    person_url = person_image.url
    clothing_url = clothing_image.url
    
    def update_progress(progress):
        """Helper to update progress if callback is provided."""
        if progress_callback:
            # Callback signature: callback(progress) - run_id is captured in closure
            progress_callback(progress)
    
    # Stage 1: Analyze (0% -> 25%)
    update_progress(0)
    analysis_result = analyze(person_url, clothing_url, preset_ids)
    update_progress(25)
    
    # Extract analysis results
    garment_description = analysis_result['garment_description']
    preset_details = analysis_result['preset_details']
    clothing_type = analysis_result['clothing_type']
    
    # Stage 2: Generate (25% -> 75%)
    # Calculate progress increment per preset for generation
    num_presets = len(preset_details)
    if num_presets == 0:
        raise Exception("No valid presets found for the given IDs and gender")
    
    progress_per_preset_generate = 50 / num_presets  # 50% total for generation stage (25% -> 75%)
    
    generate_results = []
    generated_image_urls = []
    
    for i, preset_detail in enumerate(preset_details):
        # Generate image for this preset
        generated_image_bytes = generate(
            model_image_url=person_url,
            clothing_image_url=clothing_url,
            preset_detail=preset_detail,
            garment_description=garment_description
        )
        
        # Upload generated image to Supabase
        filename = generate_uuid_filename()
        uploaded_url = upload_image_to_supabase(generated_image_bytes, filename)
        
        # Store generated image URL for enhance step
        generated_image_urls.append(uploaded_url)
        
        # Store result info for intermediate outputs
        generate_results.append({
            'preset_id': preset_detail['preset_id'],
            'preset_name': preset_detail['name'],
            'output_url': uploaded_url
        })
        
        # Update progress
        current_progress = 25 + int((i + 1) * progress_per_preset_generate)
        update_progress(min(current_progress, 75))
    
    update_progress(75)
    
    # Stage 3: Enhance (75% -> 100%)
    # Calculate progress increment per preset for enhancement
    progress_per_preset_enhance = 25 / num_presets  # 25% total for enhancement stage (75% -> 100%)
    
    final_images = []
    enhance_results = []
    
    for i, generated_url in enumerate(generated_image_urls):
        # Enhance the generated image
        enhanced_image_bytes = enhance(
            generated_image_url=generated_url,
            clothing_type=clothing_type
        )
        
        # Upload enhanced image to Supabase
        filename = generate_uuid_filename()
        uploaded_url = upload_image_to_supabase(enhanced_image_bytes, filename)
        
        # Create Image object for final output
        final_image = Image(url=uploaded_url)
        final_images.append(final_image)
        
        # Store result info
        enhance_results.append({
            'preset_id': preset_details[i]['preset_id'],
            'preset_name': preset_details[i]['name'],
            'output_url': uploaded_url
        })
        
        # Update progress
        current_progress = 75 + int((i + 1) * progress_per_preset_enhance)
        update_progress(min(current_progress, 100))
    
    update_progress(100)
    
    intermediate_outputs = {
        'step_analyze': analysis_result,
        'step_generate': generate_results,
        'step_enhance': enhance_results
    }
    
    return {
        'analysis': analysis_result,
        'intermediate_outputs': intermediate_outputs,
        'outputs': final_images
    }
