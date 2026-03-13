import os
import json
import time
from google import genai

def generate_carousel_content(article):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Aborting content generation.")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Act as an engaging, viral medical science communicator for Instagram.
    I will provide a medical news article or past research paper. You need to summarize it into a highly attention-grabbing Instagram carousel (10th-grade reading level).
    Your goal is to MAXIMIZE viewers, followers, likes, and comments. Make the discovery sound fascinating, life-changing, or mind-blowing.
    
    Article Title: {article.get('title', '')}
    Article Publish Date: {article.get('publish_date', '')}
    Article Abstract: {article.get('abstract', '')}
    Source URL: {article.get('url', 'PubMed')}

    STRICT RULES:
    1. AVOID using these characters in ANY of the output text: semicolon (;), asterisk (*), and long dashes (—). Use commas, periods, or simple hyphens instead.
    2. CONTENT SLIDES (Slide 1-2) MUST BE 50-60 WORDS EACH. This is the sweet spot for maximum reader retention.
    3. IMPORTANT: Use <b>bold tags</b> around key medical terms or viral findings within the slide body.
    4. Each content slide MUST consist of natural, full sentences. DO NOT use titles like 'STEP 1:' inside the body paragraph.
    5. CAPTION REQUIREMENTS:
       - Start with a viral, hooking title.
       - Provide a punchy summary (strictly 100-150 words).
       - End with 'Hit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀'
       - Include 10-15 viral hashtags PLUS 5-10 hyper-niche hashtags.
     
     6. SMART FIRST COMMENT (VIRAL ENGAGEMENT):
        - Create a 'first_comment' field.
        - Generate a provocative question or a "Mind-Blowing Bonus Fact" related to the article.
        - The goal is to make people want to reply. Keep it under 100 characters.
    
    7. IMAGE PROMPT (CRITICAL - HYPER-REALISM):
       - Create an 'image_prompt' for an AI image generator (professional medical photography).
    
    7. THEME COLOR: Choose 'blue', 'purple', 'green', or 'red' based on the topic.
    
    Respond STRICTLY in JSON format matching this schema:
    {{
      "cover": "A hyper-specific, attention-grabbing title (Outcome-First). Mandatory: Use 'Meme-Style' factual hooks. Example: 'LUNGS REGENERATE AFTER 20 YEARS SCARRING 🫁🔥' or 'THIS CRYSTAL REPAIRS BRAIN NEURONS IN 5 MINS 🧠✨'. Avoid vague words like 'Discovery', 'New', 'Research', 'Breakthrough'.",
      "slide_1_title": "THE BREAKTHROUGH: 3-word punchy header",
      "slide_1_body": "50-60 word natural explanation of the discovery with <b>bold</b> terms...",
      "slide_2_title": "THE IMPACT: 3-word header",
      "slide_2_body": "50-60 word explanation of what this means for the patient or future with <b>bold</b> terms...",
      "slide_4_question": "A provocative, direct question to the reader (e.g. 'Would you trust an AI doctor?' - max 60 chars)",
      "reel_script": "A punchy, 1-sentence hook for a 15-second Reel (matches cover).",
      "video_keywords": ["keyword1", "keyword2"] (kept for fallback).",
      "caption": "PUNCHY TITLE\n\nFull engaging description summary + specialty hashtags",
      "first_comment": "PROVOCATIVE QUESTION OR BONUS FACT",
      "image_prompt": "Sensory-rich, hyper-realistic photography prompt",
      "theme_color": "blue | purple | green | red"
    }}
    """
    
    # Multi-Tier Text Generation Strategy
    # Order: 2.5 Pro (Premier) -> 2.0 Flash (Advanced) -> Flash Latest (Reliability)
    text_models = [
        {"name": "gemini-2.5-pro", "label": "Gemini 2.5 Pro (Premier)"},
        {"name": "gemini-2.0-flash", "label": "Gemini 2.0 Flash (Advanced)"},
        {"name": "gemini-flash-latest", "label": "Gemini Flash Latest (Reliability/Quota)"}
    ]
    
    for model_info in text_models:
        model_name = model_info["name"]
        model_label = model_info["label"]
        
        # 2 retry attempts per model tier for reliability
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"Calling {model_label} (Attempt {attempt + 1}/{max_retries})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].strip()
                    
                data = json.loads(text)
                print(f"Success: Content generated using {model_label}")
                return data
                
            except Exception as e:
                error_msg = str(e)
                print(f"{model_label} Error (Attempt {attempt + 1}): {error_msg}")
                
                # If rate limited (429), wait and retry THIS model tier
                if "429" in error_msg and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    print(f"Rate limited for {model_name}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # For any other error or if all retries for this tier fail, move to next model
                break
    
    print("CRITICAL: All text generation models failed or exhausted.")
    return None


if __name__ == "__main__":
    # Test
    sample = {
        'title': "Hidden metabolism found operating inside the cell nucleus",
        'publish_date': "2026-03-09",
        'abstract': "Researchers have found hundreds of metabolic enzymes attached to human DNA inside the cell nucleus. Different tissues and cancers show unique patterns of these enzymes, forming a nuclear metabolic fingerprint."
    }
    print(json.dumps(generate_carousel_content(sample), indent=2))
