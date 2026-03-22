import os
import json
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

from fetcher import get_top_article
from processor import generate_carousel_content
from image_generator import generate_carousel_images
from publisher import publish_carousel
from image_gen_service import generate_ai_image, has_valid_image_asset

# Load env file in local development, GH actions will use secrets
load_dotenv()

PIPELINE_ROUND = "18 (Carousel Only)"
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

def save_posted(posted_list):
    temp_file = POSTED_FILE + '.tmp'
    try:
        with open(temp_file, 'w') as f:
            json.dump(posted_list, f, indent=2)
        os.replace(temp_file, POSTED_FILE)
    except Exception as e:
        print(f"Error saving posted articles: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

def _caption_excerpt(text, max_words=24):
    words = (text or "").replace("\n", " ").split()
    return " ".join(words[:max_words]).strip()

def _trim_history(items, max_items=150):
    if len(items) <= max_items:
        return items
    return items[-max_items:]

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

def run_pipeline(dry_run=False, mock=False, post_carousel=True):
    print(f"\n=== Starting Medical News Bot Pipeline (Round {PIPELINE_ROUND}) ===")
    if dry_run:
        print("⚠️  DRY RUN MODE ENABLED: No posts will be sent to Instagram.")
    if mock:
        print("🎭 MOCK MODE ENABLED: Bypassing Gemini AI to save quota.")
    
    # 0. Setup directories
    media_dir = "media"
    os.makedirs(media_dir, exist_ok=True)

    # 0. Cleanup old media
    cleanup_old_media(media_dir)

    needs_instagram = not dry_run

    # Pre-check credentials
    if needs_instagram and not os.getenv("IG_SESSION") and (not os.getenv("IG_USERNAME") or not os.getenv("IG_PASSWORD")):
        print("Error: Missing Instagram credentials and IG_SESSION. Aborting.")
        return

    # 1. Fetch & Process
    article = None
    slides_data = None
    article_context = None

    posted_data = load_posted()

    publish_succeeded = dry_run

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
            "first_comment": "Bonus fact!"
        }
        article = {"id": "mock-123", "title": "Mock Article"}
    else:
        article = get_top_article(posted_data)
        if not article:
            print("No new articles found.")
            return
        print(f"Selected Article: {article['title']}")
        slides_data = generate_carousel_content(article, recent_history=posted_data)

    if article:
        article_context = " ".join(
            part for part in [
                article.get('title', ''),
                article.get('abstract', ''),
                article.get('journal', ''),
            ] if part
        )
    
    if not slides_data:
        print("Error: Content generation failed.")
        return

    # 2. Carousel Output
    if post_carousel:
        print("--- Processing Academic Carousel ---")
        c_data = slides_data.get('carousel_data', slides_data)
        
        # Round 39: AI Image Generation
        unique_id = int(time.time())
        bg_image = os.path.join(media_dir, f"ai_gen_carousel_{unique_id}.jpg")
        ai_bg = generate_ai_image(
            c_data['image_prompt'],
            bg_image,
            article_context=article_context,
            article_url=article.get('url') if article else None,
        ) if not mock else None

        if not mock and not ai_bg and has_valid_image_asset(bg_image):
            print("✅ Using validated recovered image from disk after fallback chain.")
            ai_bg = bg_image

        if not mock and (not ai_bg or not has_valid_image_asset(ai_bg)):
            print("❌ Error: No validated article-relevant image was found. Skipping this post instead of publishing a no-image carousel.")
            return
        
        image_paths = generate_carousel_images(c_data, ai_bg, media_dir)
        if image_paths:
            # Round 52: Use absolute paths and verify files
            abs_image_paths = []
            for p in image_paths:
                if os.path.exists(p):
                    f_size = os.path.getsize(p)
                    print(f"DEBUG: Generated Slide: {os.path.basename(p)} ({f_size} bytes)")
                    if f_size > 1000: # Basic check for non-empty image
                        abs_image_paths.append(os.path.abspath(p))
                
            if len(abs_image_paths) == len(image_paths):
                publish_succeeded = publish_carousel(
                    abs_image_paths, 
                    c_data['caption'], 
                    dry_run=dry_run,
                    first_comment=slides_data.get('first_comment')
                )
            else:
                print(f"❌ Error: Some carousel images are missing or empty! ({len(abs_image_paths)}/{len(image_paths)})")
                publish_succeeded = False

    if not mock and article and post_carousel and publish_succeeded:
        # Update metadata for tracking
        article_id = article.get('id')
        
        # Find existing or create new
        entry = next((i for i in posted_data if (i['id'] if isinstance(i, dict) else i) == article_id), None)
        if not entry or not isinstance(entry, dict):
            entry = {
                "id": article_id, 
                "title": article.get('title'),
                "timestamp": datetime.now().isoformat()
            }
            posted_data.append(entry)
            
        if post_carousel:
            entry['posted_as_carousel'] = True
            carousel = slides_data.get("carousel_data", {})
            entry['cover'] = carousel.get('cover')
            entry['image_prompt'] = carousel.get('image_prompt')
            entry['slide_titles'] = [
                carousel.get('slide_1_title'),
                carousel.get('slide_2_title'),
            ]
            entry['caption_excerpt'] = _caption_excerpt(carousel.get('caption', ''))
            entry['url'] = article.get('url')
            entry['journal'] = article.get('journal')

        # Filter out old entry placeholder if it was just an ID string, 
        # and re-insert the updated dict entry.
        final_posted = []
        appended = False
        for item in posted_data:
            item_id = item['id'] if isinstance(item, dict) else item
            if item_id == article_id:
                if not appended:
                    final_posted.append(entry)
                    appended = True
            else:
                final_posted.append(item)

        save_posted(_trim_history(final_posted))
    elif not mock and article and post_carousel:
        print("Skipping posted-state update because the publish step did not complete successfully.")

    print("Pipeline finished successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Medical News Bot')
    parser.add_argument('--dry-run', action='store_true', help='No real posting')
    parser.add_argument('--mock', action='store_true', help='Bypass AI')
    parser.add_argument('--carousel', action='store_true', help='Enable carousel')
    parser.add_argument('--carousel-only', action='store_true', help='Post carousel only')
    
    args = parser.parse_args()
    
    p_carousel = args.carousel or args.carousel_only
    
    if not p_carousel:
        p_carousel = True
        
    run_pipeline(dry_run=args.dry_run, mock=args.mock, post_carousel=p_carousel)
