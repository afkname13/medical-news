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
    1. AVOID using these characters in ANY of the output text: semicolon (;), asterisk (*), and long dashes (—). Use commas, periods, or simple hyphens instead.
    2. CONTENT SLIDES (Slide 1-3) MUST BE 60-80 WORDS EACH. This is critical for depth. Expand on the "why" and "how".
    3. IMPORTANT: Use <b>bold tags</b> around key medical terms or mind-blowing findings within the slide body (e.g., 'Scientists found <b>hundreds of metabolic enzymes</b>...').
    4. Each content slide MUST have a context-specific CATCHY TITLE using the format 'CATCHY TITLE: Body text'.
    5. CAPTION MUST BE BETWEEN 1800 AND 2100 CHARACTERS:
       - Start with a viral, hooking title.
       - Provide a comprehensive, easy-to-read summary of the research (4-5 solid paragraphs).
       - Include a section '🔬 RESEARCH CITATION:' followed by the full title and date.
       - End with 'Hit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀'
       - Include a massive block of viral, relevant hashtags (30+ hashtags) for maximum reach.
       - IMPORTANT: Do NOT exceed 2100 characters in total for the caption.
    
    Respond STRICTLY in JSON format matching this schema:
    {{
      "cover": "Short, punchy, viral title (under 50 chars). E.g. 'CELL\\'S SECRET ENGINE UNLOCKED!'",
      "slide_1": "CATCHY TITLE: Detailed 60-80 word explanation with <b>bold</b> terms...",
      "slide_2": "CATCHY TITLE: Detailed 60-80 word explanation with <b>bold</b> terms...",
      "slide_3": "CATCHY TITLE: Detailed 60-80 word explanation with <b>bold</b> terms...",
      "caption": "1800-2100 char elite summary + research citation + CTA + mega hashtag block"
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
        "caption": f"Amazing new discovery in the medical field: {article.get('title', '')}. What are your thoughts? Drop a comment below! #medical #science #discovery"
    }

if __name__ == "__main__":
    # Test
    sample = {
        'title': "Hidden metabolism found operating inside the cell nucleus",
        'publish_date': "2026-03-09",
        'abstract': "Researchers have found hundreds of metabolic enzymes attached to human DNA inside the cell nucleus. Different tissues and cancers show unique patterns of these enzymes, forming a nuclear metabolic fingerprint."
    }
    print(json.dumps(generate_carousel_content(sample), indent=2))
