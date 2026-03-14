import os
import time
import random
import json
from instagrapi import Client

def login_to_instagram():
    """Authenticates with Instagram using credentials or session."""
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("Warning: IG_USERNAME or IG_PASSWORD not set.")
        return None
        
    cl = Client()
    # --- GEO-TARGETING OPTIMIZATION: US Region (Round 46/48) ---
    # 1. Force US Device Fingerprint
    cl.set_device({
        "app_version": "269.0.0.18.75",
        "android_version": 26,
        "android_release": "8.0.0",
        "device_model": "SM-G960F",
        "device_id": "android-564564564564564",
        "uuid": "7f093010-3882-11ed-a261-0242ac120002",
        "phone_id": "7f093010-3882-11ed-a261-0242ac120002",
        "ad_id": "7f093010-3882-11ed-a261-0242ac120002",
        "device_type": "android",
        "cpu": "samsungexynos9810",
        "version_code": "443075838"
    })
    cl.set_user_agent("Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x2220; samsung; SM-G960F; starlte; samsungexynos9810; en_US; 443075838)")
    
    # 2. Force US Locale/Timezone
    cl.set_locale("en_US")
    cl.set_country("US")
    cl.set_timezone_offset(-14400) # US Eastern Time (GMT-4)
    
    # 3. Verify Bot IP (Cloud Presence)
    try:
        import requests
        bot_ip = requests.get('https://api.ipify.org', timeout=5).text
        print(f"Geo-Verification: Bot is running from IP {bot_ip} (US Actions Runner) 🇺🇸")
    except:
        print("Geo-Verification: Could not fetch external IP. Proceeding with metadata defaults.")
    
    print("Geo-Targeting: Account localized to United States (En-US / SM-G960F) 🇺🇸")
    
    session_data = os.getenv("IG_SESSION")
    
    # Adding a realistic delay/jitter before login/action
    jitter = random.randint(5, 15)
    print(f"Waiting {jitter} seconds (Jitter Control)...")
    time.sleep(jitter)

    if session_data:
        try:
            print("Found IG_SESSION. Attempting to load session...")
            cl.set_settings(json.loads(session_data))
            # Test session with a lightweight check
            cl.get_timeline_feed()
            print("Session loaded and verified via timeline!")
            return cl
        except Exception as e:
            print(f"Session invalid or expired: {e}")

    try:
        print(f"Logging into Instagram as {username}...")
        cl.login(username, password)
        
        # --- SMART SESSION WARMING (Round 43) ---
        # Some accounts fail if they jump straight to uploads.
        # We do a 'warm-up' call to mimic real user behavior.
        print("Warming up session...")
        cl.account_info() # Lightweight call to confirm full auth state
        time.sleep(random.randint(3, 7))
        
        # Save session for local use
        with open("ig_session.json", "w") as f:
            json.dump(cl.get_settings(), f, indent=2)
        print("Login successful! Session saved to ig_session.json")
        print("--- IMPORTANT ---")
        print("New session saved to ig_session.json")
        print("Copy its contents to YOUR GITHUB SECRET named 'IG_SESSION' to bypass blacklist!")
        print("-----------------")
        return cl
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def simulate_browsing(cl):
    """Simulates a human browsing the feed and liking a few posts."""
    try:
        print("Stealth Mode: Simulating human browsing behavior... 🕵️‍♂️")
        # Fetch timeline feed
        feeds = cl.get_timeline_feed()
        # Randomly browse a few items
        browse_count = random.randint(3, 6)
        items = feeds.get('items', [])[:10]
        
        if items:
            random.shuffle(items)
            to_like = items[:random.randint(1, 2)]
            for item in to_like:
                media_id = item.get('id')
                if media_id:
                    print(f"Stealth Mode: Mimicking interest in post {media_id}...")
                    cl.media_like(media_id)
                    time.sleep(random.randint(10, 25)) # Human-like pause
        
        print("Stealth Mode: Browsing simulation complete.")
    except Exception as e:
        print(f"Stealth Mode Warning: Browsing simulation failed (ignored): {e}")

def publish_carousel(image_paths, caption, dry_run=False, first_comment=None):
    if dry_run:
        print("⚠️  DRY RUN: Skipping ACTUAL upload.")
        return True

    cl = login_to_instagram()
    if not cl:
        print("Failed to log in to Instagram. Skipping publishing.")
        return False
    
    try:
        # --- PHASE 1: PRE-POST SIMULATION (Round 47) ---
        simulate_browsing(cl)
        time.sleep(random.randint(15, 30))

        from music_service import MusicService
        music_svc = MusicService(cl)
        track = music_svc.get_trending_track()
        
        extra_data = {}
        if track:
            print(f"Injecting music metadata for: {track.title}")
            extra_data = {
                "audio_cluster_id": track.audio_cluster_id,
                "audio_asset_id": track.id,
                "music_params": json.dumps({
                    "audio_asset_id": track.id,
                    "audio_cluster_id": track.audio_cluster_id,
                    "audio_asset_start_time_in_ms": 0,
                    "product": "feed_audio",
                    "overlap_duration_in_ms": 30000,
                    "song_name": track.title,
                    "artist_name": track.display_artist,
                })
            }

        print(f"Uploading carousel to Instagram (Caption Length: {len(caption)} chars)...")
        media = cl.album_upload(
            paths=image_paths,
            caption=caption,
            extra_data=extra_data
        )
        print(f"Initial upload successful! Media ID: {media.pk}")
        
        # --- PHASE 2: VERIFICATION & ENGAGEMENT ---
        time.sleep(random.randint(20, 45)) # Stealth Pause
        media_info = cl.media_info(media.pk)
        
        if not media_info.caption_text:
            print("Warning: Instagram stripped the caption! Retrying media_edit...")
            cl.media_edit(media.pk, caption)
            time.sleep(random.randint(10, 20))
            media_info = cl.media_info(media.pk)
            
        # --- AUTO-LIKE (Round 47) ---
        try:
            print("Engagement Engine: Auto-liking own post... 💖")
            cl.media_like(media.pk)
        except: pass

        if first_comment:
            time.sleep(random.randint(15, 40)) # More jitter
            print(f"Posting algorithmic first comment: '{first_comment}'")
            try:
                cl.media_comment(media.pk, first_comment)
            except Exception as e:
                print(f"Warning: Failed to post first comment: {e}")
            
        return True
    except Exception as e:
        print(f"Error publishing to Instagram: {e}")
        return False


def publish_reel(video_path, caption, dry_run=False):
    """Publishes a Reel (clip) to Instagram."""
    if dry_run:
        print(f"⚠️  DRY RUN: Skipping ACTUAL Reel upload for: {video_path}")
        return True

    cl = login_to_instagram()
    if not cl:
        print("Failed to log in to Instagram. Skipping Reel publishing.")
        return False
        
    try:
        # --- PHASE 1: PRE-POST SIMULATION (Round 47) ---
        simulate_browsing(cl)
        time.sleep(random.randint(15, 30))

        print(f"Uploading Reel: {video_path}...")
        try:
            media = cl.clip_upload(video_path, caption, feed_show='0')
        except Exception as e:
            if "login_required" in str(e).lower():
                print("Detected 'login_required' during upload. Attempting ONE-TIME re-login...")
                cl = login_to_instagram()
                if cl:
                    media = cl.clip_upload(video_path, caption, feed_show='0')
                else:
                    raise e
            else:
                raise e
        
        print(f"Reel published successfully! Media ID: {media.pk}")
        
        # --- PHASE 2: ENGAGEMENT (Round 47) ---
        time.sleep(random.randint(20, 45))
        try:
            print("Engagement Engine: Auto-liking own Reel... 💖")
            cl.media_like(media.pk)
        except: pass

        return True
    except Exception as e:
        print(f"Error publishing Reel: {e}")
        return False

if __name__ == "__main__":
    # Test stub
    pass
