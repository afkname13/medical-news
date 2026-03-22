import os
import json
import time
import re
from difflib import SequenceMatcher
from google import genai

LAST_CONTENT_REPORT = {}

FORBIDDEN_HOOK_PHRASES = [
    "the truth is out",
    "it has finally happened",
    "everything changed",
    "this changes everything",
    "no one saw this coming",
]

FALLBACK_HOOKS = [
    "NEW BREAKTHROUGH",
    "JUST REVEALED",
    "SCIENTISTS FOUND",
    "MAJOR DISCOVERY",
    "RESEARCH ALERT",
]

DEFAULT_HASHTAGS = [
    "#medicalnews",
    "#healthnews",
    "#medicalbreakthrough",
    "#scienceupdate",
    "#futureofmedicine",
    "#biotech",
    "#researchnews",
    "#breakingnews",
    "#viralnews",
    "#healthyliving",
    "#longevity",
    "#wellness",
    "#medtok",
    "#healthtok",
    "#explorepage",
    "#viral",
]

COVER_TEASE_MAP = {
    "cancer": "CANCER HUNTERS",
    "tumor": "TUMOR ALERT",
    "brain": "BRAIN SIGNAL",
    "heart": "HEART WATCH",
    "gene": "GENE TRACKERS",
    "genetic": "GENE TRACKERS",
    "chromosome": "CHROMOSOME WATCH",
    "aging": "AGING ALERT",
    "bacteria": "MICROBE HUNTERS",
    "immune": "IMMUNE ALERT",
    "alzheimer": "MEMORY ALERT",
    "adhd": "BRAIN WATCH",
}

def _strip_html(text):
    return re.sub(r'<[^>]+>', '', text or '')

def _split_sentences(text):
    cleaned = re.sub(r'\s+', ' ', _strip_html(text)).strip()
    if not cleaned:
        return []
    parts = re.split(r'(?<=[.!?])\s+', cleaned)
    return [part.strip() for part in parts if part.strip()]

def _truncate_words(text, max_words):
    words = text.split()
    return " ".join(words[:max_words]).strip()

def _make_cover_from_title(title):
    title_words = re.findall(r"[A-Za-z0-9']+", (title or "").upper())
    tease = _choose_cover_tease(title)
    punch = " ".join(title_words[:4]) if title_words else "MEDICAL SHIFT"
    return _repair_cover_text(f"{tease}\n{punch}")

def _choose_cover_tease(title):
    lowered = (title or "").lower()
    for keyword, tease in COVER_TEASE_MAP.items():
        if keyword in lowered:
            return tease
    return FALLBACK_HOOKS[hash(title or "cover") % len(FALLBACK_HOOKS)]

def build_hashtags(article):
    title = (article.get('title', '') + " " + article.get('abstract', '')).lower()
    tags = list(DEFAULT_HASHTAGS)

    keyword_map = {
        "cancer": "#cancerresearch",
        "tumor": "#oncology",
        "heart": "#hearthealth",
        "cardio": "#cardiology",
        "brain": "#brainhealth",
        "adhd": "#adhd",
        "alzheimer": "#alzheimers",
        "gene": "#genetics",
        "ai": "#aiinhealthcare",
        "smartwatch": "#digitalhealth",
        "wearable": "#wearabletech",
        "diabetes": "#diabetes",
        "sleep": "#sleephealth",
        "chromosome": "#geneticsresearch",
        "aging": "#agingresearch",
        "male": "#menshealth",
        "women": "#womenshealth",
        "blood": "#hematology",
    }

    for keyword, tag in keyword_map.items():
        if keyword in title and tag not in tags:
            tags.append(tag)

    engagement_tags = [
        "#fyp", "#foryou", "#learnontiktok", "#mustread", "#healthfacts",
        "#science", "#medicine", "#medicalresearch", "#healthtips",
    ]
    for tag in engagement_tags:
        if tag not in tags:
            tags.append(tag)

    return tags[:18]

def append_citation_and_hashtags(caption, article):
    citation_parts = []
    if article.get("journal"):
        citation_parts.append(article["journal"])
    if article.get("publish_date"):
        citation_parts.append(article["publish_date"])
    citation_line = " | ".join(citation_parts) or "Medical source"

    url = article.get("url")
    hashtags = build_hashtags(article)

    base_caption = clean_caption(caption or "")
    base_lines = [line for line in base_caption.split("\n") if line.strip()]
    non_hashtag_lines = [
        line for line in base_lines
        if not line.strip().startswith("#") and not re.fullmatch(r"[.\-\s]+", line.strip())
    ]

    rebuilt = "\n".join(non_hashtag_lines).strip()
    if rebuilt:
        rebuilt += "\n\n"
    rebuilt += f"Source: {citation_line}"
    if url:
        rebuilt += f"\nStudy link: {url}"
    rebuilt += "\n\n" + " ".join(hashtags)
    return rebuilt.strip()

def build_fallback_content(article):
    title = article.get('title', 'Medical breakthrough')
    abstract = _strip_html(article.get('abstract', ''))
    sentences = _split_sentences(abstract)
    journal = article.get('journal', 'medical research')

    if len(sentences) < 2:
        sentences = [
            f"Researchers reported a new finding linked to {title.lower()}.",
            f"The work highlights why this result may matter for patients, clinicians, and future studies.",
            f"The report came from {journal} and adds new context to the field.",
        ]

    slide_1_body = _truncate_words(" ".join(sentences[:2]), 58)
    slide_2_body = _truncate_words(" ".join(sentences[2:4]) or " ".join(sentences[:2]), 58)
    title_terms = [word.upper() for word in re.findall(r"[A-Za-z0-9']+", title)[:6]]
    prompt_terms = " ".join(re.findall(r"[A-Za-z0-9']+", title.lower())[:8])

    data = {
        "theme_color": "blue",
        "carousel_data": {
            "cover": _make_cover_from_title(title),
            "cover_cta": "TAP TO LEARN MORE",
            "slide_1_title": "WHAT THEY FOUND",
            "slide_1_body": slide_1_body,
            "slide_2_title": "WHY IT MATTERS",
            "slide_2_body": slide_2_body,
            "slide_4_question": f"Could this shift {title_terms[0].lower() if title_terms else 'medicine'} care?",
            "caption": (
                "READ THIS! 🚨\n\n"
                f"{title}\n\n"
                f"{_truncate_words(' '.join(sentences[:2]), 38)}\n\n"
                f"{_truncate_words(' '.join(sentences[2:4]) or ' '.join(sentences[:2]), 38)}\n\n"
                "Follow @medicalnews_daily for more medical science updates."
            ),
            "image_prompt": f"{prompt_terms} biomedical research laboratory scientific visualization clinical realism"
        },
        "first_comment": "What part of this finding matters most to you?"
    }
    data = normalize_generated_payload(data)
    data["carousel_data"]["caption"] = append_citation_and_hashtags(data["carousel_data"]["caption"], article)
    return data

def clean_caption(text):
    """
    Cleans the caption for Instagram:
    1. Removes <b> and </b> tags.
    2. Ensures hashtags are on new lines at the end.
    """
    if not text:
        return text
        
    # Remove HTML bold tags
    text = re.sub(r'</?b>', '', text)
    
    # Identify hashtags
    lines = text.split('\n')
    content_lines = []
    hashtags = []
    
    hashtag_pattern = re.compile(r'#\w+')
    
    for line in lines:
        if line.strip().startswith('#') or (len(hashtag_pattern.findall(line)) > 2): # Mostly hashtags
            hashtags.extend(hashtag_pattern.findall(line))
        else:
            content_lines.append(line)
    
    # Reconstruct content
    clean_text = '\n'.join(content_lines).strip()
    
    # Add hashtags block if found
    if hashtags:
        ordered_hashtags = list(dict.fromkeys(hashtags))
        # Standard Instagram aesthetic spacing
        clean_text += "\n\n.\n.\n.\n\n"
        clean_text += " ".join(ordered_hashtags)
        
    return clean_text.strip()

def _normalize_text(text):
    return re.sub(r'\s+', ' ', (text or '').strip().lower())

def _repair_cover_text(cover):
    if not cover:
        return cover

    lines = [line.strip() for line in cover.replace("\\n", "\n").split("\n") if line.strip()]
    if not lines:
        return cover

    first_line = lines[0].upper()
    for phrase in FORBIDDEN_HOOK_PHRASES:
        if phrase in first_line.lower():
            replacement = FALLBACK_HOOKS[hash(first_line) % len(FALLBACK_HOOKS)]
            lines[0] = replacement
            break

    if len(lines) == 1:
        lines.append("MEDICAL SHIFT")

    cleaned_lines = []
    for idx, line in enumerate(lines[:2]):
        words = re.findall(r"[A-Za-z0-9']+", line.upper())
        max_words = 2 if idx == 0 else 4
        cleaned_lines.append(" ".join(words[:max_words]))

    if len(cleaned_lines) < 2:
        cleaned_lines.append("MEDICAL SHIFT")

    return "\n".join(cleaned_lines[:2])

def _body_overlap_ratio(first_body, second_body):
    return SequenceMatcher(None, _normalize_text(first_body), _normalize_text(second_body)).ratio()

def _recent_history_signals(recent_history, limit=10):
    signals = []
    for entry in (recent_history or [])[-limit:]:
        if not isinstance(entry, dict):
            continue
        signals.append({
            "title": entry.get("title", ""),
            "cover": entry.get("cover", ""),
            "image_prompt": entry.get("image_prompt", ""),
            "caption_excerpt": entry.get("caption_excerpt", ""),
            "slide_titles": " ".join(entry.get("slide_titles", []) or []),
            "content_signature": entry.get("content_signature", ""),
        })
    return signals

def _similarity(a, b):
    left = _normalize_text(a)
    right = _normalize_text(b)
    if not left or not right:
        return 0
    return SequenceMatcher(None, left, right).ratio()

def validate_generated_payload(data, recent_history=None):
    errors = []

    carousel = data.get("carousel_data", {})

    cover = carousel.get("cover", "")
    cover_lower = _normalize_text(cover)
    if any(phrase in cover_lower for phrase in FORBIDDEN_HOOK_PHRASES):
        errors.append("cover uses a forbidden repetitive hook phrase")
    cover_lines = [line.strip() for line in cover.replace("\\n", "\n").split("\n") if line.strip()]
    if len(cover_lines) != 2:
        errors.append("cover must have exactly two lines")
    for idx, line in enumerate(cover_lines[:2]):
        max_words = 2 if idx == 0 else 4
        if len(re.findall(r"[A-Za-z0-9']+", line)) > max_words:
            errors.append("cover line is too long for layout")

    if carousel.get("slide_1_title") and carousel.get("slide_1_title") == carousel.get("slide_2_title"):
        errors.append("slide_1_title and slide_2_title are identical")

    overlap = _body_overlap_ratio(
        carousel.get("slide_1_body", ""),
        carousel.get("slide_2_body", ""),
    )
    if overlap > 0.72:
        errors.append("slide bodies overlap too much")

    image_prompt = _normalize_text(carousel.get("image_prompt", ""))
    if len(image_prompt.split()) < 5:
        errors.append("image prompt is too generic")

    recent_signals = _recent_history_signals(recent_history)
    for signal in recent_signals:
        if _similarity(cover, signal.get("cover", "")) > 0.76:
            errors.append("cover repeats a recent format too closely")
            break
    for signal in recent_signals:
        if _similarity(image_prompt, signal.get("image_prompt", "")) > 0.72:
            errors.append("image prompt overlaps recent visual concept")
            break
    slide_title_blob = " ".join([
        carousel.get("slide_1_title", ""),
        carousel.get("slide_2_title", ""),
    ])
    for signal in recent_signals:
        if _similarity(slide_title_blob, signal.get("slide_titles", "")) > 0.82:
            errors.append("slide titles repeat a recent post")
            break
    caption_excerpt = _normalize_text(" ".join((carousel.get("caption", "") or "").split()[:28]))
    for signal in recent_signals:
        if _similarity(caption_excerpt, signal.get("caption_excerpt", "")) > 0.74:
            errors.append("caption framing overlaps a recent post")
            break
    content_signature = _normalize_text(" ".join([
        cover,
        slide_title_blob,
        carousel.get("slide_1_body", "")[:180],
        carousel.get("slide_2_body", "")[:180],
        image_prompt,
    ]))
    for signal in recent_signals:
        if _similarity(content_signature, signal.get("content_signature", "")) > 0.76:
            errors.append("overall post concept is too close to a recent post")
            break

    return errors

def normalize_generated_payload(data, article=None):
    carousel = data.get("carousel_data", {})

    if "cover" in carousel:
        carousel["cover"] = _repair_cover_text(carousel["cover"])

    if "caption" in carousel:
        carousel["caption"] = clean_caption(carousel["caption"])
    elif "caption" in data:
        data["caption"] = clean_caption(data["caption"])

    if article and "caption" in carousel:
        carousel["caption"] = append_citation_and_hashtags(carousel["caption"], article)

    return data


def generate_carousel_content(article, recent_history=None):
    global LAST_CONTENT_REPORT
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Falling back to deterministic local content generator.")
        LAST_CONTENT_REPORT = {
            "mode": "fallback",
            "provider": "local",
            "model": None,
            "reason": "missing_gemini_api_key",
        }
        return build_fallback_content(article)
        
    client = genai.Client(api_key=api_key)
    
    recent_signals = _recent_history_signals(recent_history, limit=6)
    recent_memory = "\n".join(
        f"- Title: {item['title']} | Cover: {item['cover']} | Image: {item['image_prompt']}"
        for item in recent_signals
        if any(item.values())
    ) or "None"

    prompt = f"""
    Act as an engaging, viral medical science communicator for Instagram.
    I will provide a medical news article or past research paper. You need to summarize it into a highly attention-grabbing Instagram carousel (10th-grade reading level).
    Your goal is to MAXIMIZE viewers, followers, likes, and comments. Make the discovery sound fascinating, life-changing, or mind-blowing.
    Every output must feel fresh and specific to THIS article, not reusable boilerplate.
    
    Article Title: {article.get('title', '')}
    Article Publish Date: {article.get('publish_date', '')}
    Article Abstract: {article.get('abstract', '')}
    Source URL: {article.get('url', 'PubMed')}
    RECENT POSTS TO AVOID REPEATING:
    {recent_memory}

    STRICT RULES:
    1. AVOID using these characters in ANY of the output text: semicolon (;), asterisk (*), and long dashes (—). Use commas, periods, or simple hyphens instead.
    2. CONTENT SLIDES (Slide 1-2) MUST BE 50-60 WORDS EACH. This is the sweet spot for maximum reader retention.
    3. IMPORTANT: Use <b>bold tags</b> around key medical terms or viral findings within the slide body.
    4. Each content slide MUST consist of natural, full sentences. DO NOT use titles like 'STEP 1:' inside the body paragraph.
    5. UNIQUENESS IS MANDATORY:
       - The cover hook, slide titles, caption framing, and first comment must feel distinct from common viral templates.
       - DO NOT reuse generic hooks such as "THE TRUTH IS OUT", "IT HAS FINALLY HAPPENED", "THIS CHANGES EVERYTHING", or similar boilerplate.
       - Anchor the wording in the article's actual mechanism, disease area, patient impact, or scientific finding.
       - Slide 1 and Slide 2 must cover DIFFERENT angles. Slide 1 explains what was found. Slide 2 explains why it matters. Do not repeat the same facts in slightly different words.
29. COVER FORMAT:
       - Create a 2-line 'Topic Label + Specific Reveal' structure using a newline (\n).
       - Line 1 is a compact topic label in 1-2 words, or 2 short words. Examples: 'CANCER HUNTERS', 'AGING ALERT', 'BRAIN WATCH'.
       - Line 2 is the specific reveal in 2-4 words. Examples: 'BACTERIA HIT TUMORS', 'Y CHROMOSOME VANISHES'.
       - The first line should feel like a category tag, not a sentence.
       - **FORBIDDEN**: DO NOT use the phrase 'THE TRUTH IS OUT' or similar clickbait boilerplate.
       - TOTAL HARD LIMIT: maximum 6 words across both lines.
    
    6. SMART FIRST COMMENT (VIRAL ENGAGEMENT):
       - Create a 'first_comment' field.
       - Generate a provocative question or a "Mind-Blowing Bonus Fact" related to the article.
       - The goal is to make people want to reply. Keep it under 100 characters.
    
    7. IMAGE SEARCH KEYWORDS (PHOTOGRAPHY FOCUS):
       - **MANDATORY**: Provide a descriptive prompt that can be used for image generation AND for searching high-quality photography if generation fails.
       - **FORBIDDEN**: Absolutely NO generic anatomical icons, plastic models, or medical diagrams.
       - **FOCUS**: Name the exact subject from this article, then the setting. Good examples: "Scientists studying pancreatic beta cells in a high-tech lab", "Immune cells attacking melanoma under fluorescent microscopy", "Cardiology team reviewing MRI scans in a hospital imaging suite".
       - **STYLE**: Focus on "Cinematic Medical Photography", "Clinical Realism", or "Scientific Visual Realism".
       - The image must be directly relevant to the article, not just vaguely medical.
    
    8. THEME COLOR: Choose 'blue', 'purple', 'green', or 'red' based on the topic.
    
    9. CAPTION STYLE (CRITICAL):
       - Start with 'READ THIS! 🚨' or 'MUST READ! ⚠️'.
       - Provide a deep-dive summary (exactly 100-120 words).
       - Use massive spacing (double newlines) between points to make it easy to scan.
       - The tone should be 'Insider Alert' style.
       - **FORBIDDEN**: DO NOT use any HTML tags (like <b>) inside the "caption" field. Keep caption as plain text only.
       - **HASHTAGS**: Include them at the very end of the caption text.

    Respond STRICTLY in JSON format matching this schema:
    {{
      "theme_color": "blue | purple | green | red",
      "carousel_data": {{
        "cover": "TEASE PHRASE\nSPECIFIC BREAKTHROUGH (Max 7 words total)",
        "cover_cta": "TAP TO LEARN MORE ➔",
        "slide_1_title": "THE BREAKTHROUGH: 3-word punchy header",
        "slide_1_body": "60-70 word detailed, academic explanation of the discovery with <b>bold</b> terms...",
        "slide_2_title": "THE IMPACT: 3-word header",
        "slide_2_body": "60-70 word detailed explanation of the clinical impact with <b>bold</b> terms...",
        "slide_4_question": "A provocative, academic question (e.g. 'How will this change medicine?' - max 60 chars)",
        "caption": "READ THIS! 🚨\n\n[Academic-Viral Title]\n\n[Body Point 1]\n\n[Body Point 2]\n\n[Body Point 3]\n\nHit FOLLOW @medicalnews_daily for your daily dose of life-saving science! 🏥🚀\n\n#AcademicHashtags...",
        "image_prompt": "Ultra-specific scientific prompt (3D Molecular/Pathogen view)"
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
                data = normalize_generated_payload(data, article=article)
                validation_errors = validate_generated_payload(data, recent_history=recent_history)
                if validation_errors:
                    print(f"{model_label} validation failed: {', '.join(validation_errors)}")
                    LAST_CONTENT_REPORT = {
                        "mode": "rejected",
                        "provider": "gemini",
                        "model": model_name,
                        "reason": ", ".join(validation_errors),
                    }
                    continue

                print(f"Success: Content generated using {model_label}")
                LAST_CONTENT_REPORT = {
                    "mode": "generated",
                    "provider": "gemini",
                    "model": model_name,
                    "reason": "success",
                }
                return data
                
            except Exception as e:
                error_msg = str(e)
                print(f"{model_label} Error (Attempt {attempt + 1}): {error_msg}")
                
                # If rate limited (429), wait and retry THIS model tier
                if "429" in error_msg and (
                    "PerDay" in error_msg or
                    "limit: 0" in error_msg or
                    "RESOURCE_EXHAUSTED" in error_msg
                ):
                    break
                if "429" in error_msg and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 35 # Round 44: Aggressive backoff for Free Tier
                    print(f"Rate limited for {model_name}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # For any other error or if all retries for this tier fail, move to next model
                break
    
    print("CRITICAL: All text generation models failed or exhausted.")
    print("Falling back to deterministic local content generator.")
    LAST_CONTENT_REPORT = {
        "mode": "fallback",
        "provider": "local",
        "model": None,
        "reason": "all_models_failed_or_exhausted",
    }
    return build_fallback_content(article)

def get_last_content_report():
    return dict(LAST_CONTENT_REPORT)


if __name__ == "__main__":
    # Test
    sample = {
        'title': "Hidden metabolism found operating inside the cell nucleus",
        'publish_date': "2026-03-09",
        'abstract': "Researchers have found hundreds of metabolic enzymes attached to human DNA inside the cell nucleus. Different tissues and cancers show unique patterns of these enzymes, forming a nuclear metabolic fingerprint."
    }
    print(json.dumps(generate_carousel_content(sample), indent=2))
