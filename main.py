import os
import json
import base64
import requests
import urllib.parse
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

from fetcher import get_top_article
from processor import generate_carousel_content
from image_generator import generate_carousel_images
from publisher import publish_carousel

# Load env file in local development, GH actions will use secrets
load_dotenv()

POSTED_FILE = 'posted_articles.json'

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, 'r') as f:
            try:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
            except json.JSONDecodeError:
                return []
    return []

def save_posted(posted_list, new_article):
    # Store ID, Title, and Timestamp for variety tracking
    entry = {
        "id": new_article['id'],
        "title": new_article['title'],
        "timestamp": datetime.now().isoformat()
    }
    posted_list.append(entry)
    with open(POSTED_FILE, 'w') as f:
        json.dump(posted_list, f, indent=2)

def cleanup_old_media(media_dir, days=1):
    """Deletes media files older than 1 day to save storage."""
    print(f"Cleaning up media older than {days} days...")
    now = time.time()
    if not os.path.exists(media_dir):
        return
    for f in os.listdir(media_dir):
        f_path = os.path.join(media_dir, f)
        if os.stat(f_path).st_mtime < now - (days * 86400):
            try:
                if os.path.isfile(f_path):
                    os.remove(f_path)
                    print(f"Deleted old file: {f}")
            except Exception as e:
                print(f"Cleanup error: {e}")

def generate_gemini_image(image_prompt):
    """Generates a hyper-realistic cover image using Gemini's image generation model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Cannot generate image.")
        return None
    
    client = genai.Client(api_key=api_key)
    
    print(f"Generating Gemini AI image...")
    
    # Multi-level AI Image Generation
    # NOTE: Most Gemini Free Tier accounts have a limit of 0 for image generation.
    # We keep these here in case the account is upgraded or enabled by Google.
    models_to_try = [
        {"name": "gemini-2.0-flash", "label": "Gemini 2.0 Flash (Next-Gen)"},
        {"name": "gemini-2.5-flash-image", "label": "Gemini 2.5 Flash (Reliable)"}
    ]
    
    for model_info in models_to_try:
        model_name = model_info["name"]
        model_label = model_info["label"]
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"Generating image using {model_label} (Attempt {attempt + 1}/{max_retries})...")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                    ),
                )
                
                # Extract the image from the response
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            # Save the image locally
                            base = os.path.dirname(os.path.abspath(__file__))
                            bg_path = os.path.join(base, "media", "bg.jpg")
                            os.makedirs(os.path.dirname(bg_path), exist_ok=True)
                            
                            image_data = part.inline_data.data
                            with open(bg_path, "wb") as f:
                                f.write(image_data)
                            
                            file_size = os.path.getsize(bg_path)
                            print(f"{model_label} image saved successfully ({file_size} bytes)")
                            return bg_path
                
                print(f"{model_label}: No image data returned.")
                break # Try next model if no data
                
            except Exception as e:
                error_details = str(e)
                print(f"{model_label} Error (Attempt {attempt + 1}): {error_details}")
                
                # If rate limited, wait and retry THIS model
                if "429" in error_details and attempt < max_retries - 1:
                    print(f"Rate limited for {model_name}. Waiting 20s before retry...")
                    time.sleep(20)
                    continue
                
                # If persistent error or other failure, move to next model
                break
                
    print("All AI image models failed or exhausted. Proceeding to Unsplash fallback.")
    return None

def get_unsplash_bg(search_query):
    """Fetches a high-quality real photograph from Unsplash (fallback)."""
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    if not access_key:
        print("Warning: UNSPLASH_ACCESS_KEY not set. Using default fallback.")
        return download_image("https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop", "media/bg.jpg")
        
    url = f"https://api.unsplash.com/photos/random?query={urllib.parse.quote(search_query)}&orientation=portrait&client_id={access_key}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        img_url = data['urls']['regular']
        return download_image(img_url, "media/bg.jpg")
    except Exception as e:
        print(f"Unsplash API error: {e}")
        return download_image("https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop", "media/bg.jpg")

def download_image(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return path
    except Exception as e:
        print(f"Image download error: {e}")
    return path

def run_pipeline():
    print("\n=== Starting Medical News Bot Pipeline (Round 17) ===")
    
    # 0. Cleanup Old Storage
    base = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(base, "media")
    cleanup_old_media(media_dir)
    
    # Pre-check: Ensure we have Instagram credentials or session
    if not os.getenv("IG_SESSION") and (not os.getenv("IG_USERNAME") or not os.getenv("IG_PASSWORD")):
        print("Error: Missing Instagram credentials and IG_SESSION. Aborting pipeline early.")
        return
    
    posted_data = load_posted()
    posted_ids = [item['id'] if isinstance(item, dict) else item for item in posted_data]
    
    article = get_top_article(posted_ids)
    if not article:
        print("No suitable articles found. Exiting.")
        return
        
    print(f"Selected Article: {article['title']}")
    
    # 1. Summarize
    print("Generating AI content...")
    slides_data = generate_carousel_content(article)
    
    if not slides_data:
        print("Error: AI content generation failed. Aborting pipeline to prevent low-quality posts.")
        return
    
    # Robust caption extraction: Ensure we always have a caption
    caption = slides_data.get('caption', "")
    if not caption or len(caption) < 100:
        print("AI caption missing or too short. Generating fallback caption...")
        research_link = article.get('url', 'PubMed')
        caption = f"🚨 {article['title']} 🚨\n\nNew medical breakthrough! Swipe left for the breakdown. \n\n🔬 RESEARCH SOURCE: {article['url']}\n\nHit FOLLOW @medicalnews_daily for daily medical science! 🏥🚀"

    # Safety: Strip HTML tags from caption
    caption = caption.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
    
    # Instagram limits
    if len(caption) > 2100:
        caption = caption[:2100] + "..."
        
    print(f"Caption extracted (Length: {len(caption)} chars)")
    
    # 2. Get Background Image — Gemini AI first, Unsplash fallback
    image_prompt = slides_data.get('image_prompt', '')
    bg_path = None
    
    if image_prompt:
        bg_path = generate_gemini_image(image_prompt)
    
    if not bg_path:
        print("Gemini image failed. Falling back to Unsplash...")
        fallback_query = article['title'] + " medical"
        bg_path = get_unsplash_bg(fallback_query)

    # 3. Generate Images
    print("Generating pixel-perfect carousel images...")
    image_paths = generate_carousel_images(slides_data, bg_path, media_dir)
    if not image_paths:
        print("Failed to generate images.")
        return
        
    # 4. Publish
    print("Publishing to Instagram...")
    success = publish_carousel(image_paths, caption)
    
    if success:
        # Save to DB only on success
        save_posted(posted_data, article)
        print("Pipeline finished successfully!")
    else:
        print("Pipeline finished with publishing error.")
        
if __name__ == "__main__":
    run_pipeline()
