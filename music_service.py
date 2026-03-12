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
        # We try multiple queries in case one fails or returns bad data
        test_queries = [random.choice(self.safe_genres), "Lo-fi", "Ambient", "Chill"]
        
        for query in test_queries:
            try:
                print(f"Searching for music with query: '{query}'...")
                tracks = self.cl.search_music(query)
                
                if tracks:
                    # Filter out any None values that might have slipped through faulty extraction
                    valid_tracks = [t for t in tracks if t and hasattr(t, "title")]
                    
                    if valid_tracks:
                        # Pick one of the top 3
                        selection_pool = valid_tracks[:3]
                        track = random.choice(selection_pool)
                        print(f"Selected Track: {track.title} by {track.display_artist}")
                        return track
                
                print(f"No valid tracks found for '{query}'. Trying next...")
            except Exception as e:
                # This catches the 'NoneType' or 'KeyError' issues inside the library's extractor
                print(f"Music search failed for '{query}': {e}. Trying next fallback...")
        
        print("Music Service: All searches failed. Proceeding without music.")
        return None

if __name__ == "__main__":
    # Test stub (requires valid session/login)
    pass
