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
    1. AVOID using these characters in ANY of the output text: semicolon (;), asterisk (*), and long dashes (—). Use commas, periods, or simple hyphens instead    2. CONTENT SLIDES (Slide 1-3) MUST BE 50-60 WORDS EACH. This is the sweet spot for readability and depth.
    3. IMPORTANT: Use <b>bold tags</b> around key medical terms or viral findings within the slide body (e.g., 'Scientists found <b>hundreds of metabolic enzymes</b>...').
    4. Each content slide MUST consist of natural, full sentences. DO NOT use titles like 'CATCHY TITLE:' or 'STEP 1:' inside the body paragraph. Avoid phrases like 'Doctors embrace digital health' or 'Beyond steps' if they look like headers. The text should flow as a coherent narrative.
    5. CAPTION REQUIREMENTS:
       - Start with a viral, hooking title.
       - IMPORTANT: Add TWO NEWLINES (empty line) after the title, then start the description.
       - Provide a punchy summary (strictly 100-150 words).
       - IMPORTANT: Do NOT use any HTML tags like <b> in the caption.
       - Include '🔬 RESEARCH SOURCE:' with title, date, and link: {article.get('url', 'PubMed')}
       - End with 'Hit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀'
       - Include 20-25 viral hashtags (e.g. #fyp, #explore, #viral, #medicalnews).
    
    6. IMAGE PROMPT (CRITICAL - HYPER-REALISM):
       - Create an 'image_prompt' for an AI image generator.
       - It MUST describe a professional, hyper-realistic clinical or laboratory scene.
       - Avoid anything "AI-looking" (no glowing neon futuristic pods). Use natural lighting, shallow depth of field, and real textures (glass, steel, biological tissue).
       - Prompt should be 2-3 sentences. Include keywords: 'professional medical photography, 8k, ultra-realistic, cinematic lighting, macro lens'.
    
    7. THEME COLOR: Choose 'blue', 'purple', 'green', or 'red' based on the topic.
    
    Respond STRICTLY in JSON format matching this schema:
    {{
      "cover": "EXTREME HOOK: A punchy, high-impact title (under 45 chars). MUST use a specific number, a unique medical verb, or a direct promise (e.g. 'NEW 5-MINUTE BRAIN FIX' or 'THE END OF INSOMNIA?'). Avoid vague words like 'Discovery', 'Research', or 'Update'.",
      "slide_1_title": "THE PROBLEM: 3-word punchy header",
      "slide_1_body": "50-60 word natural explanation with <b>bold</b> terms...",
      "slide_2_title": "THE BREAKTHROUGH: 3-word header",
      "slide_2_body": "50-60 word natural explanation with <b>bold</b> terms...",
      "slide_3_title": "THE RESULTS: 3-word header",
      "slide_3_body": "50-60 word natural explanation with <b>bold</b> terms...",
      "caption": "PUNCHY TITLE\n\nFull engaging description summary + source link + hashtags",
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
