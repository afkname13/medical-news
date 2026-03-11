import os
import json
from google import genai

def generate_carousel_content(article):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Using mock content.")
        return mock_content(article)
        
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
      "cover": "Short, punchy, viral title (under 50 chars)",
      "slide_1": "50-60 word natural explanation with <b>bold</b> terms...",
      "slide_2": "50-60 word natural explanation with <b>bold</b> terms...",
      "slide_3": "50-60 word natural explanation with <b>bold</b> terms...",
      "caption": "100-150 word summary + source link + hashtags",
      "image_prompt": "Sensory-rich, hyper-realistic photography prompt",
      "theme_color": "blue | purple | green | red"
    }}
    """
    
    try:
        print("Calling Gemini API...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return mock_content(article)

def mock_content(article):
    return {
        "cover": "HUGE MEDICAL BREAKTHROUGH UNLOCKED!",
        "slide_1": f"JUST DISCOVERED: Scientists discovered something mind-blowing related to: {article.get('title', '')[:30]}.",
        "slide_2": "WHY THIS MATTERS: This shocking new finding could change lives and help millions of people in the future.",
        "slide_3": "THE FUTURE CURE: Stay tuned for more updates on this amazing discovery that left scientists stunned.",
        "caption": f"Amazing new discovery in the medical field: {article.get('title', '')}. What are your thoughts? Drop a comment below! #medical #science #discovery",
        "theme_color": "blue"
    }

if __name__ == "__main__":
    # Test
    sample = {
        'title': "Hidden metabolism found operating inside the cell nucleus",
        'publish_date': "2026-03-09",
        'abstract': "Researchers have found hundreds of metabolic enzymes attached to human DNA inside the cell nucleus. Different tissues and cancers show unique patterns of these enzymes, forming a nuclear metabolic fingerprint."
    }
    print(json.dumps(generate_carousel_content(sample), indent=2))
