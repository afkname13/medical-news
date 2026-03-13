import os
import json
import base64
import requests
import urllib.parse
import time
import argparse
import random
from datetime import datetime
from dotenv import load_dotenv

from fetcher import get_top_article
from processor import generate_carousel_content
from image_generator import generate_carousel_images
from publisher import publish_carousel, publish_reel
from music_service import search_viral_music
from video_generator import VideoGenerator

# Load env file in local development, GH actions will use secrets
load_dotenv()

PIPELINE_ROUND = "17 (Reels Beta)"
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
    entry = {
        "id": new_article.get('id', str(random.randint(1000, 9999))),
        "title": new_article.get('title', 'Unknown Title'),
        "timestamp": datetime.now().isoformat()
    }
    posted_list.append(entry)
    with open(POSTED_FILE, 'w') as f:
        json.dump(posted_list, f, indent=2)

def cleanup_old_media(media_dir, days=1):
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

def run_pipeline(dry_run=False, mock=False, post_carousel=True, post_reels=False):
    print(f"\n=== Starting Medical News Bot Pipeline (Round {PIPELINE_ROUND}) ===")
    if dry_run:
        print("⚠️  DRY RUN MODE ENABLED: No posts will be sent to Instagram.")
    if mock:
        print("🎭 MOCK MODE ENABLED: Bypassing Gemini AI to save quota.")
    
    # 0. Setup directories
    base = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(base, "media")
    os.makedirs(media_dir, exist_ok=True)
    cleanup_old_media(media_dir)
    
    # Pre-check credentials
    if not os.getenv("IG_SESSION") and (not os.getenv("IG_USERNAME") or not os.getenv("IG_PASSWORD")):
        print("Error: Missing Instagram credentials and IG_SESSION. Aborting.")
        return

    # 1. Fetch & Process
    article = None
    slides_data = None

    if mock:
        article = {
            "id": "mock_id_123",
            "title": "MOCK: The Future of Medical Automation",
            "url": "https://example.com/mock-medical"
        }
        slides_data = {
            "cover": "REVERSES 20-YEAR LUNG SCARRING",
            "slide_1_title": "THE BREAKTHROUGH",
            "slide_1_body": "Researchers from <b>Mayo Clinic</b> have discovered a specific wave of <b>near-infrared light</b> that can trigger the brain's natural repair system. This non-invasive method successfully reversed memory loss in clinical trials for the first time.",
            "slide_2_title": "THE IMPACT",
            "slide_2_body": "This technology could replace complex surgeries for <b>brain injuries</b> and neurodegenerative diseases. By 2030, 5-minute 'light therapy' sessions could become a standard treatment for <b>recovery</b> and <b>mental health</b> optimization.",
            "slide_4_question": "Would you try a 5-minute brain fix? 🤔",
            "reel_script": "This near-infrared light triggers a specific repair protein in the brain. It's reversing memory loss in clinical trials right now. The future of brain repair is light.",
            "video_keywords": ["medical lab", "brain scan", "microscope", "doctor"],
            "caption": "BRAIN REPAIR BREAKTHROUGH 🧠✨\n\nResearchers have found a way to use light waves to trigger natural brain repair. No surgery, just science.\n\nHit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀\n\n#brainrepair #mayoclinic #neuroscience #biotech #medicalnews #sciencebreakthrough #futuremedicine",
            "first_comment": "QUICK QUESTION: What's the one thing you wish your brain could do better? Let us know! 👇",
            "image_prompt": "Hyper-realistic medical laboratory, soft blue lighting, high-tech brain scanner, cinematic photography, macro shot of neural pathways glowing.",
            "theme_color": "blue"
        }
    else:
        posted_data = load_posted()
        posted_ids = [item['id'] if isinstance(item, dict) else item for item in posted_data]
        article = get_top_article(posted_ids)
        if not article:
            print("No new articles found.")
            return
        print(f"Selected Article: {article['title']}")
        slides_data = generate_carousel_content(article)
    
    if not slides_data:
        print("Error: Content generation failed.")
        return

    # 2. Shared Assets (Music)
    theme_color = slides_data.get('theme_color', 'blue')
    music_track = search_viral_music(theme_color)
    
    # 3. Carousel Output
    if post_carousel:
        print("--- Processing Carousel ---")
        image_paths = generate_carousel_images(slides_data, None, media_dir)
        if image_paths:
            publish_carousel(
                image_paths, 
                slides_data['caption'], 
                dry_run=dry_run,
                first_comment=slides_data.get('first_comment')
            )

    # --- REELS FLOW (Round 34 Pivot) ---
    if post_reels:
        print("--- Processing Meme-Style Reel ---")
        
        vg = VideoGenerator()
        
        # In Static Image Reels, we use the COVER slide from the carousel
        # If carousel was already generated, use image_paths[0]
        cover_image = None
        if post_carousel and image_paths:
            cover_image = image_paths[0]
        else:
            # Fallback: Regenerate just the cover if only Reels requested
            print("Regenerating cover for standalone Reel...")
            temp_image_paths = generate_carousel_images(slides_data, None, media_dir)
            if temp_image_paths:
                cover_image = temp_image_paths[0]

        if cover_image:
            music_path = getattr(music_track, 'local_path', None)
            final_reel = vg.create_static_reel(cover_image, music_path)
            
            if final_reel:
                publish_reel(final_reel, slides_data['caption'], dry_run=dry_run)
        else:
            print("Skipping Reel: No cover image found to freeze.")

    if not mock and (post_carousel or post_reels):
        save_posted(load_posted(), article)

    print("Pipeline finished successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Medical News Bot')
    parser.add_argument('--dry-run', action='store_true', help='No real posting')
    parser.add_argument('--mock', action='store_true', help='Bypass AI')
    parser.add_argument('--carousel', action='store_true', help='Post carousel (default)')
    parser.add_argument('--reels', action='store_true', help='Post reels')
    
    args = parser.parse_args()
    
    # Logic: if nothing specified, do carousel. If one or both specified, do those.
    p_carousel = args.carousel
    p_reels = args.reels
    if not p_carousel and not p_reels:
        p_carousel = True
        
    run_pipeline(dry_run=args.dry_run, mock=args.mock, post_carousel=p_carousel, post_reels=p_reels)
