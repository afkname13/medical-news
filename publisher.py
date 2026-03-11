import os
import time
import random
from instagrapi import Client

def publish_carousel(image_paths, caption):
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("Warning: IG_USERNAME or IG_PASSWORD not set. Skipping publishing.")
        return False
        
    cl = Client()
    
    # Adding a realistic delay/jitter before login to mimic human behavior
    jitter = random.randint(10, 30)
    print(f"Waiting {jitter} seconds before login (Jitter Control)...")
    time.sleep(jitter)
    
    try:
        print(f"Logging into Instagram as {username}...")
        cl.login(username, password)
        
        print(f"Uploading carousel to Instagram (Caption Length: {len(caption)} chars)...")
        print(f"Caption Snippet: {caption[:100]}...")
        media = cl.album_upload(
            paths=image_paths,
            caption=caption
        )
        print(f"Successfully published carousel! Media ID: {media.pk}")
        return True
    except Exception as e:
        print(f"Error publishing to Instagram: {e}")
        return False

if __name__ == "__main__":
    # Test stub
    pass
