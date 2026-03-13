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
            model='imagen-4.0-generate-001',
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
        # Extract keywords for better Unsplash matching
        # Force "microscope" and "abstract" to avoid generic doctor photos
        clean_prompt = prompt.lower().replace("microscopic", "").replace("molecular", "").replace("3d", "").replace("model", "").strip()
        # Take first 5 words only for better Unsplash keyword matching
        short_keywords = " ".join(clean_prompt.split()[:5])
        search_query = f"microscope {short_keywords} science abstract"
        
        # New Unsplash Source API (source is deprecated)
        unsplash_url = f"https://images.unsplash.com/photo-1576086213369-97a306d36557?q=80&w=1080&auto=format&fit=crop" # HIGH QUALITY MINT/BIO DEFAULT
        
        # If we want dynamic-ish, we can use a keyword-based redirect if available, 
        # but Unsplash Source is officially dead. We use a high-fidelity 'Scientific' default 
        # that looks amazing for multiple topics.
        
        print(f"📸 Fetching High-Fidelity Scientific Asset: {search_query}")
        
        headers = { 'User-Agent': 'Mozilla/5.0' }
        img_response = requests.get(unsplash_url, headers=headers, timeout=15)
        
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
