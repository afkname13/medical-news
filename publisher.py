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
    session_data = os.getenv("IG_SESSION")
    
    # Adding a realistic delay/jitter before login/action
    jitter = random.randint(5, 15)
    print(f"Waiting {jitter} seconds (Jitter Control)...")
    time.sleep(jitter)

    if session_data:
        try:
            print("Found IG_SESSION. Attempting to load session...")
            cl.set_settings(json.loads(session_data))
            # Test session
            cl.get_timeline_feed()
            print("Session loaded and verified!")
            return cl
        except Exception as e:
            print(f"Session invalid or expired: {e}")

    try:
        print(f"Logging into Instagram as {username}...")
        cl.login(username, password)
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

def publish_carousel(image_paths, caption, dry_run=False, first_comment=None):
    if dry_run:
        print("⚠️  DRY RUN: Skipping ACTUAL upload.")
        return True

    cl = login_to_instagram()
    if not cl:
        print("Failed to log in to Instagram. Skipping publishing.")
        return False
    
    try:
        from music_service import MusicService
        music_svc = MusicService(cl)
        track = music_svc.get_trending_track()
        
        extra_data = {}
        if track:
            print(f"Injecting music metadata for: {track.title}")
            # EXPERIMENTAL: This payload mimics the official app's hidden sidecar music fields
            extra_data = {
                "audio_cluster_id": track.audio_cluster_id,
                "audio_asset_id": track.id,
                "music_params": json.dumps({
                    "audio_asset_id": track.id,
                    "audio_cluster_id": track.audio_cluster_id,
                    "audio_asset_start_time_in_ms": 0,
                    "product": "feed_audio", # Key field for carousel music
                    "overlap_duration_in_ms": 30000,
                    "song_name": track.title,
                    "artist_name": track.display_artist,
                })
            }

        if dry_run:
            print("⚠️  DRY RUN: Skipping ACTUAL upload and verification.")
            print(f"Music Discovery: {track.title if track else 'None'}")
            if first_comment:
                print(f"Engagement Check: Would post First Comment: '{first_comment}'")
            return True

        print(f"Uploading carousel to Instagram (Caption Length: {len(caption)} chars)...")
        print(f"Caption Snippet: {caption[:100]}...")
        media = cl.album_upload(
            paths=image_paths,
            caption=caption,
            extra_data=extra_data
        )
        print(f"Initial upload successful! Media ID: {media.pk}")
        
        # --- ROBUST CAPTION VERIFICATION LOOP ---
        # Instagram sometimes strips captions on upload. We verify and force it if missing.
        time.sleep(5) # Give it a few seconds to process
        media_info = cl.media_info(media.pk)
        
        if not media_info.caption_text:
            print("Warning: Instagram stripped the caption! Retrying media_edit...")
            cl.media_edit(media.pk, caption)
            time.sleep(3)
            media_info = cl.media_info(media.pk)
            if media_info.caption_text:
                print("Success: Caption restored via edit!")
            else:
                print("Critical Error: Caption still missing after retry.")
        else:
            print("Verified: Caption successfully posted.")
            
        # --- FIRST COMMENT (Engagement Booster) ---
        if first_comment:
            print(f"Posting algorithmic first comment: '{first_comment}'")
            try:
                cl.media_comment(media.pk, first_comment)
                print("First comment posted successfully!")
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
        print(f"Caption: {caption[:50]}...")
        return True

    cl = login_to_instagram()
    if not cl:
        print("Failed to log in to Instagram. Skipping Reel publishing.")
        return False
        
    try:
        print(f"Uploading Reel: {video_path}...")
        media = cl.clip_upload(video_path, caption, feed_show='0')
        print(f"Reel published successfully! Media ID: {media.pk}")
        return True
    except Exception as e:
        print(f"Error publishing Reel: {e}")
        return False

if __name__ == "__main__":
    # Test stub
    pass
