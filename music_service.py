import random
from typing import Optional
from instagrapi import Client
from instagrapi.types import Track

class MusicService:
    def __init__(self, client: Client):
        self.cl = client
        # Curated keywords for trending but non-distracting medical news background
        self.safe_genres = [
            "Chill Lofi",
            "Ambient Study",
            "Deep House Instrumental",
            "Corporate Minimal",
            "Inspiring Piano",
            "Trending Kpop Instrumental",
            "Smooth RnB",
            "Modern Jazz"
        ]

    def get_trending_track(self, topic: str = "") -> Optional[Track]:
        """
        Searches for a suitable background track.
        If a topic is provided, it might try to match the mood.
        """
        try:
            # 1. Select a random safe genre/mood
            query = random.choice(self.safe_genres)
            print(f"Searching for trending music: '{query}'...")
            
            # 2. Search music via instagrapi
            tracks = self.cl.search_music(query)
            
            if not tracks:
                print(f"No tracks found for '{query}'. Trying fallback...")
                tracks = self.cl.search_music("Chill")
                
            if tracks:
                # 3. Pick one of the top 5 to ensure some variety
                selection_pool = tracks[:5]
                track = random.choice(selection_pool)
                print(f"Selected Track: {track.title} by {track.display_artist}")
                return track
                
            return None
        except Exception as e:
            print(f"Music Service Error: {e}")
            return None

if __name__ == "__main__":
    # Test stub (requires valid session/login)
    pass
