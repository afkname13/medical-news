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
    
    Respond STRICTLY in JSON format matching this schema:
    {{
      "cover": "Short, punchy, highly viral title (under 50 chars). E.g. 'CELL\\'S SECRET ENGINE UNLOCKED'",
      "slide_1": "TITLE: Body. Example -> 'JUST DISCOVERED: Scientists found a whole new factory running inside...'",
      "slide_2": "TITLE: Body. Example -> 'HOW YOUR DNA GETS REPAIRED: These enzymes quickly gather...'",
      "slide_3": "TITLE: Body. Example -> 'THE FUTURE OF CANCER FIGHTING: This reveals an unexpected connection...'",
      "caption": "An engaging Instagram caption asking a question to drive comments, with max 3 hashtags based on the zero-hashtag policy."
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
