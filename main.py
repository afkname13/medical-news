import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv

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
            return json.load(f)
    return []

def save_posted(data):
    with open(POSTED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_unsplash_bg(topic_title):
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    # Refine the search query to be highly specific to the topic
    # We strip common stop words and focus on medical/scientific keywords
    search_keywords = topic_title.replace(":", "").replace("-", " ").split()[:5]
    query = " ".join(search_keywords) + " medical abstract"
    
    if not access_key:
        print("Warning: UNSPLASH_ACCESS_KEY not found. Using static placeholder.")
        return download_image("https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop", "media/cover.png")
        
    url = f"https://api.unsplash.com/photos/random?query={urllib.parse.quote(query)}&orientation=portrait&client_id={access_key}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        img_url = data['urls']['regular']
        return download_image(img_url, "media/bg.jpg")
    except Exception as e:
        print(f"Unsplash error for query '{query}': {e}")
        # Fallback to a safe medical abstract search if specific search fails
        return download_image("https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop", "media/cover.png")

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
    print("=== Starting Medical News Bot Pipeline ===")
    posted_ids = load_posted()
    
    article = get_top_article(posted_ids)
    if not article:
        print("No suitable articles found. Exiting.")
        return
        
    print(f"Selected Article: {article['title']}")
    
    # 1. Summarize
    print("Generating AI content...")
    slides_data = generate_carousel_content(article)
    caption = slides_data.pop('caption', article['title'] + ' #medicalnews')
    
    # 2. Get Background
    print("Fetching background from Unsplash...")
    bg_path = get_unsplash_bg(article['title'])
    
    # 3. Generate Images
    print("Generating pixel-perfect carousel images...")
    base = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(base, "media")
    os.makedirs(media_dir, exist_ok=True)
    
    image_paths = generate_carousel_images(slides_data, bg_path, media_dir)
    if not image_paths:
        print("Failed to generate images.")
        return
        
    # 4. Publish
    print("Publishing to Instagram...")
    success = publish_carousel(image_paths, caption)
    
    if success:
        # Save to DB only on success
        posted_ids.append(article['id'])
        save_posted(posted_ids)
        print("Pipeline finished successfully!")
    else:
        print("Pipeline finished with publishing error.")
        
if __name__ == "__main__":
    run_pipeline()
