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
    5. EXTREME VIRAL HOOK (COVER):
       - Create a 2-line 'Tease + Punch' structure using a newline (\n).
       - Line 1 (The Tease): A punchy, news-style hook phrase. Examples: 'WE CAN'T WAIT ANY LONGER', 'NO MORE DELAYS', 'THE TRUTH IS OUT', 'IT HAS FINALLY HAPPENED'.
       - Line 2 (The Punch): The specific medical breakthrough in 4-6 words.
       - Example: "WE CAN'T WAIT ANY LONGER\nTHE ALZHEIMER'S CURE IS HERE"
    
    6. SMART FIRST COMMENT (VIRAL ENGAGEMENT):
       - Create a 'first_comment' field.
       - Generate a provocative question or a "Mind-Blowing Bonus Fact" related to the article.
       - The goal is to make people want to reply. Keep it under 100 characters.
    
    7. IMAGE PROMPT (PHOTOREALISM & SPECIFICITY MANDATE):
       - **MANDATORY**: The image MUST be 1:1 with the scientific subject.
       - **FORBIDDEN (FAILURE CASE)**: Absolutely NO generic anatomical icons, plastic models, or medical diagrams. 
       - **NEVER** show a generic heart, a generic red brain, or a head model. If you show a heart, you have FAILED.
       - **FOCUS**: Instead of the organ, show the **MICROSCOPIC** or **MOLECULAR** level of the discovery.
       - **NEGATIVE PROMPT**: No plastic, no toys, no clip-art, no stock-photo doctors, no stethoscopes.
       - **SPECIFIC VISUALS**:
         - If it's a drug: Show the "3D Molecular Architecture" or "Chemical Crystal Lattice".
         - If it's a virus: Show a "Cinematic Pathogen View" or "Cryo-EM Spike Protein model".
         - If it's a cell: Show "Scanning Electron Microscopy" or "Cross-section of the cell nucleus".
       - Vibe: "Microscopic Cinematic", "High-Tech Biological Architecture", "Cold Scientific Realism", "High-Fidelity Molecular Realism".
    
    8. THEME COLOR: Choose 'blue', 'purple', 'green', or 'red' based on the topic.
    
    9. CAPTION STYLE (CRITICAL):
       - Start with 'READ THIS! 🚨' or 'MUST READ! ⚠️'.
       - Provide a deep-dive summary (exactly 100-120 words).
       - Use massive spacing (double newlines) between points to make it easy to scan.
       - The tone should be 'Insider Alert' style.

    Respond STRICTLY in JSON format matching this schema:
    {{
      "theme_color": "blue | purple | green | red",
      "carousel_data": {{
        "cover": "TEASE PHRASE\nSPECIFIC BREAKTHROUGH (Max 10 words total)",
        "cover_cta": "TAP TO LEARN MORE ➔",
        "slide_1_title": "THE BREAKTHROUGH: 3-word punchy header",
        "slide_1_body": "60-70 word detailed, academic explanation of the discovery with <b>bold</b> terms...",
        "slide_2_title": "THE IMPACT: 3-word header",
        "slide_2_body": "60-70 word detailed explanation of the clinical impact with <b>bold</b> terms...",
        "slide_4_question": "A provocative, academic question (e.g. 'How will this change medicine?' - max 60 chars)",
        "caption": "READ THIS! 🚨\n\n[Academic-Viral Title]\n\n[Body Point 1]\n\n[Body Point 2]\n\n[Body Point 3]\n\nHit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀\n\n#AcademicHashtags...",
        "image_prompt": "Ultra-specific scientific prompt (3D Molecular/Pathogen view)"
      }},
      "reel_data": {{
        "cover": "TEASE PHRASE\nSPECIFIC BREAKTHROUGH (Max 10 words total)",
        "cover_cta": "READ THE CAPTION TO LEARN MORE ⬇️",
        "reel_script": "A PURE VIRAL 1-sentence hook for a 15-second Reel (Extreme shock value).",
        "video_keywords": ["keyword1", "keyword2"],
        "caption": "READ THIS! 🚨\n\n[Pure Viral Title]\n\n[Short Punchy Summary - 100 words]\n\nHit FOLLOW @medicalnews_daily for more viral science! 🧬🔥\n\n#ViralHashtags...",
        "image_prompt": "High-impact, cinematic visual for the Reel cover"
      }},
      "first_comment": "PROVOCATIVE QUESTION OR BONUS FACT (Shared)"
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
                    wait_time = (attempt + 1) * 35 # Round 44: Aggressive backoff for Free Tier
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
