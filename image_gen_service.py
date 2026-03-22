import os
import base64
import json
import requests
import urllib.parse
import re
from google import genai
from PIL import Image, ImageStat

IRRELEVANT_IMAGE_TERMS = [
    "doctor", "doctors", "stethoscope", "hospital bed", "waiting room",
    "clipboard", "generic anatomy", "plastic model", "stock portrait",
    "smiling patient", "medical team", "nurse", "surgeon portrait",
    "portrait", "face", "person", "people", "woman", "man"
]

IMAGE_HISTORY_FILE = "used_image_assets.json"

def _save_response_image(image_bytes, save_path):
    with open(save_path, 'wb') as f:
        f.write(image_bytes)
    return save_path

def _extract_search_query(prompt):
    """
    Convert an art-heavy model prompt into something photo-search APIs
    can actually match.
    """
    if not prompt:
        return "medical science research clinical laboratory"

    blocked_terms = [
        "8k", "hyper-realistic", "ultra-realistic", "cinematic lighting",
        "biological realism", "microscopic detail", "anti-generic",
        "no plastic models", "high-impact", "cold scientific realism"
    ]

    cleaned = prompt
    for term in blocked_terms:
        cleaned = cleaned.replace(term, "")

    cleaned = " ".join(cleaned.replace(",", " ").split())
    return f"{cleaned} medical science research clinical laboratory"

def _load_used_assets():
    if not os.path.exists(IMAGE_HISTORY_FILE):
        return []
    try:
        with open(IMAGE_HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def _save_used_assets(items):
    trimmed = items[-200:]
    with open(IMAGE_HISTORY_FILE, "w") as f:
        json.dump(trimmed, f, indent=2)

def _remember_asset(source, asset_id, asset_url, query):
    history = _load_used_assets()
    history.append({
        "source": source,
        "asset_id": str(asset_id),
        "asset_url": asset_url,
        "query": query,
    })
    _save_used_assets(history)

def _seen_asset(source, asset_id=None, asset_url=None):
    history = _load_used_assets()
    for item in history:
        if item.get("source") != source:
            continue
        if asset_id and item.get("asset_id") == str(asset_id):
            return True
        if asset_url and item.get("asset_url") == asset_url:
            return True
    return False

def _extract_relevance_terms(prompt, article_context=None):
    text = " ".join(filter(None, [article_context, prompt])).lower()
    words = re.findall(r"[a-zA-Z]{4,}", text)
    stop_words = {
        "with", "from", "that", "this", "into", "inside", "using", "create",
        "image", "medical", "science", "research", "clinical", "visual",
        "instagram", "avoid", "prefer", "strong", "clear", "article",
        "study", "scientists", "scientist", "breakthrough"
    }
    unique = []
    for word in words:
        if word in stop_words:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:8]

def _build_search_queries(prompt, article_context=None):
    prompt_query = _extract_search_query(prompt)
    article_terms = _extract_relevance_terms("", article_context)
    combined_terms = _extract_relevance_terms(prompt, article_context)
    queries = []

    def add_query(text):
        normalized = " ".join(text.split())
        if normalized and normalized not in queries:
            queries.append(normalized)

    if article_terms:
        add_query(" ".join(article_terms[:5] + ["medical research laboratory"]))
        add_query(" ".join(article_terms[:4] + ["biomedical microscopy"]))
        add_query(" ".join(article_terms[:4] + ["scientific visualization"]))

    add_query(prompt_query)
    if combined_terms:
        add_query(" ".join(combined_terms[:4] + ["clinical research"]))

    if article_context:
        add_query(f"{article_context} medical research")

    return queries[:5]

def _image_has_visual_content(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 5000:
            return False
        with Image.open(path) as img:
            img = img.convert("RGB")
            if img.width < 400 or img.height < 400:
                return False
            stat = ImageStat.Stat(img)
            extrema = img.getextrema()
            if all(channel[0] == channel[1] for channel in extrema):
                return False
            # Reject near-flat images that are effectively blank.
            if max(stat.stddev) < 8:
                return False
        return True
    except Exception:
        return False

def _download_image(url, save_path):
    response = requests.get(url, timeout=20)
    if response.status_code != 200:
        return None
    _save_response_image(response.content, save_path)
    if _image_has_visual_content(save_path):
        return save_path
    try:
        os.remove(save_path)
    except OSError:
        pass
    return None

def _generate_with_openai(prompt, save_path, article_context=None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    enhanced_prompt = (
        f"{prompt}. Article context: {article_context or 'medical research update'}. "
        "Create a highly relevant scientific visual for an Instagram medical news post. "
        "The subject must match the article topic closely. Avoid generic doctors, hospitals, waiting rooms, clip art, plastic anatomy, and unrelated stock imagery. "
        "Prefer scientific realism, clear focal subject, and clean portrait composition."
    )

    models = []
    preferred_model = os.getenv("OPENAI_IMAGE_MODEL")
    if preferred_model:
        models.append(preferred_model)
    for model_name in ["gpt-image-1", "gpt-image-1-mini"]:
        if model_name not in models:
            models.append(model_name)

    for model_name in models:
        try:
            print(f"🎨 Generating AI image with OpenAI {model_name}...")
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "prompt": enhanced_prompt,
                    "size": "1024x1536",
                    "quality": "medium",
                    "output_format": "jpeg",
                },
                timeout=120,
            )

            if response.status_code != 200:
                print(f"⚠️ OpenAI {model_name} failed: {response.status_code} {response.text[:400]}")
                continue

            payload = response.json()
            images = payload.get("data", [])
            if not images:
                print(f"⚠️ OpenAI {model_name} returned no images.")
                continue

            image_b64 = images[0].get("b64_json")
            if image_b64:
                _save_response_image(base64.b64decode(image_b64), save_path)
                if _image_has_visual_content(save_path):
                    print(f"✅ OpenAI image generated successfully: {save_path}")
                    return save_path
                try:
                    os.remove(save_path)
                except OSError:
                    pass
        except Exception as e:
            print(f"⚠️ OpenAI {model_name} failed: {str(e)}")

    return None

def _photo_matches_context(photo_blob, relevance_terms):
    haystack = " ".join(str(photo_blob).lower().split())
    if any(term in haystack for term in IRRELEVANT_IMAGE_TERMS):
        return False
    if not relevance_terms:
        return True
    matches = sum(1 for term in relevance_terms if term in haystack)
    min_matches = 2 if len(relevance_terms) >= 3 else 1
    return matches >= min_matches

def _photo_score(photo_blob, relevance_terms):
    haystack = " ".join(str(photo_blob).lower().split())
    score = 0
    for term in relevance_terms:
        if term in haystack:
            score += 3
    for term in IRRELEVANT_IMAGE_TERMS:
        if term in haystack:
            score -= 5
    return score

def generate_ai_image(prompt, save_path, article_context=None):
    """
    Attempts AI image generation first.
    Falls back to stock photography search if generation fails or is unavailable.
    """

    # Strategy 1: OpenAI image generation
    openai_path = _generate_with_openai(prompt, save_path, article_context=article_context)
    if openai_path:
        return openai_path

    # Strategy 2: Gemini image generation
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        enhanced_prompt = (
            f"{prompt}. Create a polished medical-science visual for an Instagram post. "
            "Avoid generic anatomy icons, toy-like renders, flat clip art, and stock doctor poses. "
            "Prefer cinematic scientific realism, clear subject separation, and strong vertical composition."
        )
        image_models = [
            "gemini-2.5-flash-image",
        ]

        for model_name in image_models:
            try:
                print(f"🎨 Generating AI image with {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[enhanced_prompt],
                )

                for part in getattr(response, "parts", []) or []:
                    inline_data = getattr(part, "inline_data", None)
                    image_bytes = getattr(inline_data, "data", None)
                    if image_bytes:
                        _save_response_image(image_bytes, save_path)
                        if _image_has_visual_content(save_path):
                            print(f"✅ Gemini image generated successfully: {save_path}")
                            return save_path

                print(f"⚠️ {model_name} returned no image payload. Trying fallback model...")
            except Exception as e:
                print(f"⚠️ {model_name} failed: {str(e)}")

    else:
        print("⚠️ GEMINI_API_KEY not found. Skipping AI image generation.")

    search_queries = _build_search_queries(prompt, article_context)
    relevance_terms = _extract_relevance_terms(prompt, article_context)

    # Strategy 3: Unsplash API (Primary fallback - photography)
    try:
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if access_key:
            headers = {"Authorization": f"Client-ID {access_key}"}
            for search_query in search_queries:
                print(f"📸 Searching Unsplash with query: {search_query}")
                search_url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(search_query)}&per_page=15&orientation=portrait"
                s_response = requests.get(search_url, headers=headers, timeout=15)
                if s_response.status_code != 200:
                    continue
                results = s_response.json().get("results", [])
                if not results:
                    continue

                fresh_results = [
                    photo for photo in results
                    if not _seen_asset("unsplash", asset_id=photo.get("id"), asset_url=photo.get("urls", {}).get("regular"))
                ]
                ranked_results = [
                    photo for photo in fresh_results
                    if _photo_matches_context(photo, relevance_terms)
                ]
                if not ranked_results:
                    ranked_results = sorted(
                        fresh_results,
                        key=lambda photo: _photo_score(photo, relevance_terms),
                        reverse=True
                    )

                ranked_results = [photo for photo in ranked_results if _photo_score(photo, relevance_terms) > 0]
                for photo in ranked_results[:5]:
                    asset_url = photo["urls"]["regular"]
                    print(f"✅ Found Unsplash photo candidate: {photo['id']} by {photo['user']['name']}")
                    downloaded_path = _download_image(asset_url, save_path)
                    if downloaded_path:
                        _remember_asset("unsplash", photo.get("id"), asset_url, search_query)
                        print(f"✅ Unsplash Asset successful: {save_path}")
                        return downloaded_path
    except Exception as e:
        print(f"⚠️ Unsplash strategy failed: {str(e)}")

    # Strategy 4: Pexels API (Backup Strategy)
    try:
        pexels_key = os.getenv("PEXELS_API_KEY")
        if pexels_key:
            headers = {"Authorization": pexels_key}
            for search_query in search_queries:
                print(f"🔄 Searching Pexels with query: {search_query}")
                search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(search_query)}&per_page=10&orientation=portrait"
                p_response = requests.get(search_url, headers=headers, timeout=15)
                if p_response.status_code != 200:
                    continue
                photos = p_response.json().get("photos", [])
                if not photos:
                    continue

                fresh_photos = [
                    photo for photo in photos
                    if not _seen_asset("pexels", asset_id=photo.get("id"), asset_url=photo.get("src", {}).get("large2x"))
                ]
                ranked_photos = [
                    photo for photo in fresh_photos
                    if _photo_matches_context(photo, relevance_terms)
                ]
                if not ranked_photos:
                    ranked_photos = sorted(
                        fresh_photos,
                        key=lambda photo: _photo_score(photo, relevance_terms),
                        reverse=True
                    )

                ranked_photos = [photo for photo in ranked_photos if _photo_score(photo, relevance_terms) > 0]
                for photo in ranked_photos[:5]:
                    asset_url = photo["src"]["large2x"]
                    print(f"✅ Found Pexels photo candidate: {photo['id']}")
                    downloaded_path = _download_image(asset_url, save_path)
                    if downloaded_path:
                        _remember_asset("pexels", photo.get("id"), asset_url, search_query)
                        print(f"✅ Pexels Asset successful: {save_path}")
                        return downloaded_path
    except Exception as e:
        print(f"⚠️ Pexels strategy failed: {str(e)}")

    print("⚠️ No relevant image asset found. Falling back to gradient-only card rendering.")
    return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Test
    generate_ai_image("A cinematic 3D molecular visualization of a sildenafil molecule interacting with mitochondrial enzymes inside a human cell.", "media/test_ai_gen.jpg")
