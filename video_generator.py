import os
import requests
import random
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip
from moviepy.config import change_settings

# Note: ImageMagick is often required for MoviePy TextClip on some systems.
# On GitHub Actions, we might need a specific setup or use an alternative.
# For now, we'll implement the logic and handle fallbacks.

from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoGenerator:
    def __init__(self):
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.output_dir = "media"
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_text_image(self, text, size, fontsize=60, color=(255, 255, 255)):
        """Creates a transparent PNG with text using PIL."""
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load a default font
        try:
            # Try to find a common bold font
            font_paths = [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, fontsize)
                    break
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Wrap text manually if needed (very basic)
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # check width
            w = draw.textlength(" ".join(current_line), font=font)
            if w > size[0] * 0.9:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        line_height = fontsize * 1.2
        y = (size[1] - len(lines) * line_height) / 2
        for line in lines:
            w = draw.textlength(line, font=font)
            x = (size[0] - w) / 2
            # Draw shadow for readability
            draw.text((x+3, y+3), line, font=font, fill=(0, 0, 0, 180))
            draw.text((x, y), line, font=font, fill=color)
            y += line_height
            
        return np.array(img)

    def fetch_pexels_video(self, keywords):
        # ... (same as before)
        if not self.pexels_api_key:
            print("PEXELS_API_KEY not found. Skipping video fetch.")
            return None

        query = " ".join(keywords) if isinstance(keywords, list) else keywords
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=10"
        headers = {"Authorization": self.pexels_api_key}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            videos = data.get("videos", [])
            if not videos:
                print(f"No videos found for query: {query}")
                return None

            video_data = random.choice(videos)
            video_files = video_data.get("video_files", [])
            best_file = None
            for f in video_files:
                if f.get("file_type") == "video/mp4":
                    if not best_file or f.get("width", 0) > best_file.get("width", 0):
                        best_file = f
            
            if not best_file:
                return None

            video_url = best_file.get("link")
            video_path = os.path.join(self.output_dir, f"raw_reel_bg_{int(time.time())}.mp4")
            
            print(f"Downloading Pexels video: {video_url}")
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return video_path
        except Exception as e: # Changed generic except to specific Exception
            print(f"Error fetching Pexels video: {e}") # Added error message
            return None

    def _download_viral_audio(self):
        """Downloads a royalty-free medical-lofi track for fallback from a randomized library."""
        # Round 49: Expanded library for variety
        FALLBACK_LIBRARY = [
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3"
        ]
        
        url = random.choice(FALLBACK_LIBRARY)
        # Use simple hash of URL to avoid re-downloading if already present
        import hashlib
        name = hashlib.md5(url.encode()).hexdigest()[:8]
        audio_path = os.path.join(self.output_dir, f"fallback_{name}.mp3")
        
        if os.path.exists(audio_path):
            return audio_path
            
        try:
            print(f"Downloading Viral Lo-fi Library Asset: {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            with open(audio_path, 'wb') as f:
                f.write(r.content)
            return audio_path
        except Exception as e:
            print(f"Failed to download lofi: {e}")
            return None

    def create_static_reel(self, image_path, music_path=None, duration=15):
        """Creates a Reel from a flat image (meme-style hook)."""
        unique_id = int(time.time())
        output_path = os.path.join(self.output_dir, f"final_reel_{unique_id}.mp4")
        
        # Audio Fallback Logic (Round 38)
        if not music_path or not os.path.exists(music_path):
            print("No trending audio provided. Using Viral Lo-fi Fallback...")
            music_path = self._download_viral_audio()

        try:
            print(f"Creating static Reel from: {image_path}...")
            # Load static image as a clip
            clip = ImageClip(image_path).set_duration(duration)
            clip = clip.set_fps(30) # Round 38: Smoother FPS for IG
            
            # Add Music
            if music_path and os.path.exists(music_path):
                print(f"Syncing hardcoded audio: {music_path}")
                audio = AudioFileClip(music_path).subclip(0, duration)
                clip = clip.set_audio(audio)
            else:
                print("Warning: Creating Reel WITHOUT audio (all fallbacks failed).")
            
            # Write file with professional settings
            clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=30,
                preset="veryslow", # Higher quality compression
                bitrate="5000k"
            )
            print(f"Static Reel ready: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error creating static Reel: {e}")
            return None

    def create_reel(self, video_path, text_script, music_path, output_path="media/final_reel.mp4"):
        """Assembles the Reel using MoviePy + PIL (No ImageMagick)."""
        try:
            clip = VideoFileClip(video_path)
            duration = min(clip.duration, 15)
            clip = clip.subclip(0, duration)
            
            if music_path and os.path.exists(music_path):
                audio = AudioFileClip(music_path)
                audio = audio.subclip(0, duration)
                clip = clip.set_audio(audio)

            # Create Text Overlay via PIL
            txt_img = self._create_text_image(text_script, (clip.w, clip.h), fontsize=70)
            txt_clip = ImageClip(txt_img).set_duration(duration).set_position('center')
            
            # Combine
            final_clip = CompositeVideoClip([clip, txt_clip])

            # Write Output
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
            return output_path

        except Exception as e:
            print(f"Error creating Reel: {e}")
            return None

if __name__ == "__main__":
    # Test Block
    gen = VideoGenerator()
    # Mock test
    # video = gen.fetch_pexels_video(["modern laboratory", "medical research"])
    print("Video Generator Module Initialized.")
