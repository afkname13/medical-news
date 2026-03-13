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
from image_gen_service import generate_ai_image

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

    media_dir = "media"
    os.makedirs(media_dir, exist_ok=True)

    # 0. Cleanup old media
    cleanup_old_media(media_dir)

    # Pre-check credentials
    if not os.getenv("IG_SESSION") and (not os.getenv("IG_USERNAME") or not os.getenv("IG_PASSWORD")):
        print("Error: Missing Instagram credentials and IG_SESSION. Aborting.")
        return

    # 1. Fetch & Process
    article = None
    slides_data = None

    if mock:
        print("Using MOCK content...")
        slides_data = {
            "theme_color": "blue",
            "carousel_data": {
                "cover": "TEASE\nPUNCH",
                "cover_cta": "TAP TO LEARN MORE ➔",
                "slide_1_title": "BREAKTHROUGH",
                "slide_1_body": "Mock academic info...",
                "slide_2_title": "IMPACT",
                "slide_2_body": "Mock academic impact...",
                "slide_4_question": "Mock question?",
                "caption": "READ THIS! 🚨\n\nAcademic caption...",
                "image_prompt": "Cinematic 3D molecular visualization of a sildenafil molecule interacting with mitochondrial enzymes inside a human cell, hyper-realistic, 8k, biological realism."
            },
            "reel_data": {
                "cover": "TEASE\nPUNCH",
                "cover_cta": "READ CAPTION ⬇️",
                "reel_script": "Pure viral hook!",
                "video_keywords": ["medical"],
                "caption": "READ THIS! 🚨\n\nViral caption...",
                "image_prompt": "Ultra-realistic microscopic view of mitochondrial enzyme activity triggered by a molecular catalyst, cinematic lighting, cold scientific realism."
            },
            "first_comment": "Bonus fact!"
        }
        article = {"id": "mock-123", "title": "Mock Article"}
    else:
        posted_data = load_posted()
        exclude_ids = []
        for item in posted_data:
            art_id = item['id'] if isinstance(item, dict) else item
            metadata = item if isinstance(item, dict) else {}
            
            # Smart isolation: skip already posted in the SPECIFIC requested format
            if post_carousel and not post_reels:
                if metadata.get('posted_as_carousel'): exclude_ids.append(art_id)
            elif post_reels and not post_carousel:
                if metadata.get('posted_as_reel'): exclude_ids.append(art_id)
            elif post_carousel and post_reels:
                if metadata.get('posted_as_carousel') and metadata.get('posted_as_reel'):
                    exclude_ids.append(art_id)
            else:
                # If neither carousel nor reels are explicitly requested, or if both are,
                # we exclude if it's been posted in any format.
                # This case should ideally not be hit if post_carousel or post_reels is True.
                # If both are False, then nothing will be posted anyway.
                exclude_ids.append(art_id)

        article = get_top_article(exclude_ids)
        if not article:
            print("No new articles found.")
            return
        print(f"Selected Article: {article['title']}")
        slides_data = generate_carousel_content(article)
    
    if not slides_data:
        print("Error: Content generation failed.")
        return

    # 2. Shared Assets (Music Discovery)
    theme_color = slides_data.get('theme_color', 'blue')
    music_track = search_viral_music(theme_color)
    
    # 3. Carousel Output
    if post_carousel:
        print("--- Processing Academic Carousel ---")
        c_data = slides_data.get('carousel_data', slides_data)
        
        # Round 39: AI Image Generation
        bg_image = os.path.join(media_dir, "ai_gen_carousel.jpg")
        ai_bg = generate_ai_image(c_data['image_prompt'], bg_image) if not mock else None
        
        image_paths = generate_carousel_images(c_data, ai_bg, media_dir)
        if image_paths:
            publish_carousel(
                image_paths, 
                c_data['caption'], 
                dry_run=dry_run,
                first_comment=slides_data.get('first_comment')
            )

    # 4. Reels Flow
    if post_reels:
        print("--- Processing Pure Viral Reel ---")
        r_data = slides_data.get('reel_data', slides_data)
        vg = VideoGenerator()
        
        print("Generating Reels-specific cover image...")
        # Round 39: AI Image Generation
        bg_image_reel = os.path.join(media_dir, "ai_gen_reel.jpg")
        prompt_reel = r_data.get('image_prompt', r_data.get('Image Prompt', 'Microscopic biological architecture, cinematic lighting'))
        ai_bg_reel = generate_ai_image(prompt_reel, bg_image_reel) if not mock else None
        
        reel_image_paths = generate_carousel_images(r_data, ai_bg_reel, media_dir)
        
        if reel_image_paths:
            cover_image = reel_image_paths[0]
            # HARDCODED AUDIO: Round 38 fix for silent reels
            # We use a local file if available, or fetch a sample
            music_path = getattr(music_track, 'local_path', None)
            
            final_reel = vg.create_static_reel(cover_image, music_path)
            if final_reel:
                publish_reel(final_reel, r_data['caption'], dry_run=dry_run)
        else:
            print("Skipping Reel: No cover image generated.")

    if not mock and (post_carousel or post_reels):
        # Update metadata for tracking
        posted_data = load_posted()
        article_id = article.get('id')
        
        # Find existing or create new
        entry = next((i for i in posted_data if (i['id'] if isinstance(i, dict) else i) == article_id), None)
        if not entry or not isinstance(entry, dict):
            entry = {"id": article_id, "title": article.get('title')}
            posted_data.append(entry)
            
        if post_carousel: entry['posted_as_carousel'] = True
        if post_reels: entry['posted_as_reel'] = True
        
        # We need to remove the old entry if it exists and add the updated one
        # This ensures we don't have duplicates and the latest metadata is saved.
        posted_data = [item for item in posted_data if (item['id'] if isinstance(item, dict) else item) != article_id]
        posted_data.append(entry)

        with open(POSTED_FILE, 'w') as f:
            json.dump(posted_data, f, indent=2)

    print("Pipeline finished successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Medical News Bot')
    parser.add_argument('--dry-run', action='store_true', help='No real posting')
    parser.add_argument('--mock', action='store_true', help='Bypass AI')
    parser.add_argument('--carousel', action='store_true', help='Enable carousel')
    parser.add_argument('--reels', action='store_true', help='Enable reels')
    parser.add_argument('--carousel-only', action='store_true', help='Post carousel only')
    parser.add_argument('--reels-only', action='store_true', help='Post reels only')
    
    args = parser.parse_args()
    
    # Round 39 FIX: Strict isolation. No more unintended carousels.
    p_carousel = args.carousel or args.carousel_only
    p_reels = args.reels or args.reels_only
    
    # Only default to carousel if NO flags are provided
    if not p_carousel and not p_reels:
        p_carousel = True
        
    run_pipeline(dry_run=args.dry_run, mock=args.mock, post_carousel=p_carousel, post_reels=p_reels)
