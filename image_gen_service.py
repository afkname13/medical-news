import os
import base64
import requests
from google import genai
from google.genai import types

def generate_ai_image(prompt, save_path):
    """
    Attempts to generate a hyper-realistic medical image using Gemini Imagen 3.
    Falls back to high-quality Unsplash medical photography if API fails or is restricted.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.")
        return None

    client = genai.Client(api_key=api_key)
    
    # Strategy 1: Attempt Gemini Imagen 4.0/3.0
    try:
        print(f"🎨 Generating AI Image for prompt: {prompt[:100]}...")
        # Add cinematic styling to the prompt
        enhanced_prompt = f"{prompt}, hyper-realistic, 8k resolution, cinematic lighting, biological realism, microscopic detail, anti-generic, no plastic models."
        
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                include_rai_reason=True,
                output_mime_type="image/jpeg"
            )
        )
        
        if response and response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            print(f"✅ AI Image generated successfully: {save_path}")
            return save_path
            
    except Exception as e:
        print(f"⚠️ Gemini Imagen failed: {str(e)}")
        print("🔄 Falling back to Unsplash high-fidelity medical photography...")

    # Strategy 2: High-Quality Unsplash Fallback
    try:
        # Curated list of high-fidelity medical/science Unsplash assets to avoid repetition
        FALLBACK_ASSETS = [
            "https://images.unsplash.com/photo-1576086213369-97a306d36557", # Mint/Bio
            "https://images.unsplash.com/photo-1530026405186-ed1f139313f8", # Blue/Scientific
            "https://images.unsplash.com/photo-1559757175-5700dde675bc", # Microscopic Red
            "https://images.unsplash.com/photo-1532187875605-1ef6c237ddc4", # Lab Blue
            "https://images.unsplash.com/photo-1581093588401-fbb62a02f120", # Biotech Blue
            "https://images.unsplash.com/photo-1505751172676-43ad27a3f46b", # Lab Tech
            "https://images.unsplash.com/photo-1579154236599-c1a3b3a105ac", # Cells Abstract
            "https://images.unsplash.com/photo-1576086476234-1103be98f096", # Medical Research
            "https://images.unsplash.com/photo-1511174511562-5f7f18b874f8", # Lab Glass
            "https://images.unsplash.com/photo-1584036561566-baf2418e3308"  # Biology Abstract
        ]
        
        import random
        asset_url = random.choice(FALLBACK_ASSETS) + "?q=80&w=1080&auto=format&fit=crop"
        
        print(f"🔄 AI failed. Fetching Dynamic Scientific Asset")
        
        headers = { 'User-Agent': 'Mozilla/5.0' }
        img_response = requests.get(asset_url, headers=headers, timeout=15)
        
        if img_response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            print(f"✅ Scientific Asset Fallback successful: {save_path}")
            return save_path
        else:
            print(f"❌ Asset fetch failed (Status {img_response.status_code})")
            
    except Exception as e:
        print(f"❌ Final fallback failed: {str(e)}")
        
    return None

if __name__ == "__main__":
    # Test
    generate_ai_image("A cinematic 3D molecular visualization of a sildenafil molecule interacting with mitochondrial enzymes inside a human cell.", "media/test_ai_gen.jpg")
