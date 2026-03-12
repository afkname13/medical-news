import os
import time
import random
import json
from instagrapi import Client

def publish_carousel(image_paths, caption):
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("Warning: IG_USERNAME or IG_PASSWORD not set. Skipping publishing.")
        return False
        
    cl = Client()
    
    # 1. Check for session environment variable
    session_data = os.getenv("IG_SESSION")
    if session_data:
        try:
            print("Found IG_SESSION. Attempting to load session...")
            session_dict = json.loads(session_data)
            cl.set_settings(session_dict)
            print("Session loaded successfully!")
        except Exception as e:
            print(f"Error loading session from environment: {e}")
    
    # Adding a realistic delay/jitter before login/action
    jitter = random.randint(5, 15)
    print(f"Waiting {jitter} seconds (Jitter Control)...")
    time.sleep(jitter)
    
    try:
        # 2. Check login status
        is_logged_in = False
        try:
            if session_data:
                # Simple check if current session is valid
                cl.get_timeline_feed() 
                is_logged_in = True
                print("Confirmed: Existing session is VALID. Skipping login.")
        except:
            print("Existing session is INVALID or expired. Proceeding to login...")

        if not is_logged_in:
            print(f"Logging into Instagram as {username}...")
            cl.login(username, password)
            
            # Save the new session to a local file for the user to extract
            print("Login successful! Saving session to ig_session.json...")
            with open("ig_session.json", "w") as f:
                json.dump(cl.get_settings(), f, indent=2)
            print("--- IMPORTANT ---")
            print("New session saved to ig_session.json")
            print("Copy its contents to YOUR GITHUB SECRET named 'IG_SESSION' to bypass blacklist!")
            print("-----------------")
        
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
            print("Warning: Instagram stripped the caption! Retrying with media_edit...")
            cl.media_edit(media.pk, caption)
            time.sleep(3)
            media_info = cl.media_info(media.pk)
            if media_info.caption_text:
                print("Success: Caption restored via edit!")
            else:
                print("Critical Error: Caption still missing after retry.")
        else:
            print("Verified: Caption successfully posted.")
            
        return True
    except Exception as e:
        print(f"Error publishing to Instagram: {e}")
        return False

if __name__ == "__main__":
    # Test stub
    pass
