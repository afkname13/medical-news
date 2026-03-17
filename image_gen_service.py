import os
import base64
import requests
import time
import urllib.parse
import random
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
    
    # Strategy 1: Attempt Gemini Imagen
    ai_models = ['imagen-3.0-generate-001', 'imagen-3.0-fast-001', 'imagen-3.0-generate-002']
    
    for model_name in ai_models:
        try:
            print(f"🎨 Generating AI Image for prompt using {model_name}...")
            # Add cinematic styling to the prompt
            enhanced_prompt = f"{prompt}, hyper-realistic, 8k resolution, cinematic lighting, biological realism, microscopic detail, anti-generic, no plastic models."
            
            response = client.models.generate_images(
                model=model_name,
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
                print(f"✅ AI Image generated successfully ({model_name}): {save_path}")
                return save_path
                
        except Exception as e:
            print(f"⚠️ {model_name} failed: {str(e)}")

    # Strategy 2: Unsplash API (High Quality Photography)
    try:
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if access_key:
            print("🔄 Using Unsplash API for high-quality medical asset...")
            query = f"{prompt} medical research science"
            search_url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page=10&orientation=portrait"
            headers = {"Authorization": f"Client-ID {access_key}"}
            
            s_response = requests.get(search_url, headers=headers, timeout=15)
            if s_response.status_code == 200:
                results = s_response.json().get("results", [])
                if results:
                    photo = random.choice(results)
                    asset_url = photo["urls"]["regular"]
                    print(f"✅ Found Unsplash photo: {photo['id']}")
                    
                    img_response = requests.get(asset_url, timeout=15)
                    if img_response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(img_response.content)
                        print(f"✅ Unsplash Asset successful: {save_path}")
                        return save_path
    except Exception as e:
        print(f"⚠️ Unsplash fallback failed: {str(e)}")

    # Strategy 3: Pexels API (Additional Photography Source)
    try:
        pexels_key = os.getenv("PEXELS_API_KEY")
        if pexels_key:
            print("🔄 Unsplash failed/unavailable. Trying Pexels API...")
            query = f"{prompt} clinic medicine"
            search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=10&orientation=portrait"
            headers = {"Authorization": pexels_key}
            
            p_response = requests.get(search_url, headers=headers, timeout=15)
            if p_response.status_code == 200:
                photos = p_response.json().get("photos", [])
                if photos:
                    photo = random.choice(photos)
                    asset_url = photo["src"]["large2x"]
                    print(f"✅ Found Pexels photo: {photo['id']}")
                    
                    img_response = requests.get(asset_url, timeout=15)
                    if img_response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(img_response.content)
                        print(f"✅ Pexels Asset successful: {save_path}")
                        return save_path
    except Exception as e:
        print(f"⚠️ Pexels fallback failed: {str(e)}")

    # Strategy 4: Legacy Hardcoded Fallback
    try:
        FALLBACK_IDS = [
            "1576086213369-97a306d36557", "1530026405186-ed1f139313f8",
            "1559757175-5700dde675bc", "1532187875605-1ef6c237ddc4",
            "1581093588401-fbb62a02f120", "1505751172676-43ad27a3f46b",
            "1579154236599-c1a3b3a105ac", "1576086476234-1103be98f096",
            "1511174511562-5f7f18b874f8", "1584036561566-baf2418e3308"
        ]
        
        photo_id = random.choice(FALLBACK_IDS)
        asset_url = f"https://images.unsplash.com/photo-{photo_id}?q=80&w=1080&auto=format&fit=crop"
        print(f"🔄 All dynamic fallbacks failed. Fetching Hardcoded Scientific Asset: {photo_id}")
        
        img_response = requests.get(asset_url, timeout=15)
        if img_response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            return save_path
            
    except Exception as e:
        print(f"❌ Final fallback failed: {str(e)}")
        
    return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Test
    generate_ai_image("A cinematic 3D molecular visualization of a sildenafil molecule interacting with mitochondrial enzymes inside a human cell.", "media/test_ai_gen.jpg")
