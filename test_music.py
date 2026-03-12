import os
import json
import time
from dotenv import load_dotenv
from instagrapi import Client
from music_service import MusicService

def test_music_only():
    print("\n🎵 === MUSIC-ONLY TEST ENGINE (No AI / No Images) === 🎵")
    load_dotenv()
    
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    session_data = os.getenv("IG_SESSION")

    if not username and not session_data:
        print("Error: No credentials found in .env")
        return

    cl = Client()
    # STEALTH MODE: Use a real-looking android device settings
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

    # 1. Load Session
    if session_data:
        try:
            print("Loading IG_SESSION...")
            cl.set_settings(json.loads(session_data))
            print("Session loaded!")
        except Exception as e:
            print(f"Session load error: {e}")

    try:
        # 2. Verify / Login
        is_logged_in = False
        try:
            if session_data:
                cl.get_timeline_feed()
                is_logged_in = True
                print("Session is valid.")
        except:
            print("Session invalid. Attempting fresh login...")

        if not is_logged_in:
            print(f"Logging in as {username}...")
            cl.login(username, password)
            print("Login successful!")

        # 3. Test Music Logic
        print("\n--- Testing Mega-Patch Music Discovery ---")
        music_svc = MusicService(cl)
        track = music_svc.get_trending_track()

        if track:
            print(f"\n✅ SUCCESS: Music Discovery is Working!")
            print(f"Track: {track.title}")
            print(f"Artist: {track.display_artist}")
            print(f"Cluster ID: {track.audio_cluster_id}")
            if getattr(track, 'is_trending_in_clips', False):
                print("🔥 STATUS: TRULY TRENDING")
        else:
            print("\n❌ FAILED: No track returned. Check logs above.")

    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")

if __name__ == "__main__":
    test_music_only()
