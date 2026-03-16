import os
from image_generator import generate_carousel_images

content = {
    "cover": "CELL'S SECRET ENGINE",
    "slide_1_title": "BREAKTHROUGH",
    "slide_1_body": "Content body for slide 1...",
    "slide_2_title": "IMPACT",
    "slide_2_body": "Content body for slide 2...",
    "slide_4_question": "What do you think?",
    "caption": "Test caption."
}

def run():
    media_dir = "media"
    os.makedirs(media_dir, exist_ok=True)
    paths = generate_carousel_images(content, None, media_dir)
    print(f"Generated: {paths}")

if __name__ == "__main__":
    run()
