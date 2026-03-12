import random
from typing import Optional
from instagrapi import Client
from instagrapi.types import Track

class MusicService:
    def __init__(self, client: Client):
        self.cl = client
        # High-growth keywords focused on virality
        self.viral_genres = [
            "Viral Tik Tok",
            "Trending Billboard",
            "Top Charts 2024",
            "Viral Instrumental",
            "Trending Kpop",
            "Modern Pop Instrumental"
        ]
        self.safe_genres = [
            "Chill Lofi",
            "Ambient Study",
            "Inspiring Piano",
            "Deep House Instrumental"
        ]

    def get_trending_track(self, topic: str = "") -> Optional[Track]:
        """
        Searches for a high-growth trending track.
        Prioritizes tracks explicitly marked as trending by Instagram.
        """
        # Prioritize viral queries, then fallback to safe ones
        test_queries = [random.choice(self.viral_genres), "Viral", "Trending", random.choice(self.safe_genres)]
        
        for query in test_queries:
            try:
                print(f"Searching for VIRAL music with query: '{query}'...")
                tracks = self.cl.search_music(query)
                
                if tracks:
                    # Filter and Sort: Put tracks with 'is_trending_in_clips' at the top
                    valid_tracks = [t for t in tracks if t and hasattr(t, "title")]
                    
                    if valid_tracks:
                        # Sort by trending flag (True comes first)
                        valid_tracks.sort(key=lambda x: getattr(x, 'is_trending_in_clips', False), reverse=True)
                        
                        # If the top track is trending, take it immediately!
                        if getattr(valid_tracks[0], 'is_trending_in_clips', False):
                            track = valid_tracks[0]
                            print(f"🔥 TRENDING TRACK FOUND: {track.title} by {track.display_artist}")
                            return track
                            
                        # Otherwise pick from the top 3 for variety
                        selection_pool = valid_tracks[:3]
                        track = random.choice(selection_pool)
                        print(f"Selected Track: {track.title} by {track.display_artist}")
                        return track
                
                print(f"No valid tracks found for '{query}'. Trying next...")
            except Exception as e:
                print(f"Music search failed for '{query}': {e}. Trying next...")
        
        print("Music Service: All viral searches failed. Proceeding without music.")
        return None

if __name__ == "__main__":
    # Test stub (requires valid session/login)
    pass
