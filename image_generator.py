import os
import time
import urllib.parse
import base64
import requests
from playwright.sync_api import sync_playwright

def sanitize_display_text(text):
    if not text:
        return ""

    try:
        if "Ã" in text or "â" in text:
            repaired = text.encode("latin1", "ignore").decode("utf-8", "ignore")
            if repaired:
                text = repaired
    except Exception:
        pass

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        "™": "",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    return text.strip()

def generate_html(slides_data, bg_image_url, base_dir):
    """Generates the HTML file for each slide."""

    logo_path = "https://ui-avatars.com/api/?name=Med+News&background=58D68D&color=fff&rounded=true&size=200" # Placeholder if no physical logo
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                padding: 0;
                width: 1080px;
                height: 1350px;
                font-family: 'Inter', sans-serif;
                background-color: #0D1117;
                overflow: hidden;
                position: relative;
            }
            .bg-layer {
                position: absolute;
                top: 0; left: 0; width: 1080px; height: 1350px;
                background-color: #0D1117; /* Default background */
                background: linear-gradient(135deg, #0D1621 0%, #1A2634 50%, #0D1117 100%); /* Medical Deep Gradient */
                z-index: 1;
            }
            .bg-soft {
                position: absolute;
                top: 0; left: 0; width: 1080px; height: 1350px;
                z-index: 1;
                overflow: hidden;
            }
            .bg-soft img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                filter: blur(34px);
                transform: scale(1.08);
                opacity: 0.72;
            }
            .bg-layer img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                opacity: 0.92;
            }
            .bg-layer.blurred {
                filter: blur(60px);
                transform: scale(1.1);
                opacity: 0.6;
            }
            .overlay {
                position: absolute;
                top: 0; left: 0; width: 1080px; height: 1350px;
                background:
                    linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.05) 36%, rgba(0,0,0,0.14) 65%, rgba(0,0,0,0.34) 100%);
                z-index: 2;
            }
            .cover-overlay {
                position: absolute;
                top: 0; left: 0; width: 1080px; height: 1350px;
                background:
                    linear-gradient(180deg, rgba(0,0,0,0.04) 0%, rgba(0,0,0,0.08) 42%, rgba(0,0,0,0.22) 72%, rgba(0,0,0,0.58) 100%);
                z-index: 2;
            }
            
            /* Logo */
            .logo {
                position: absolute;
                top: 50px; right: 50px;
                width: 162px; /* 15% of 1080 */
                height: 162px;
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 50%;
                background-image: url('logo.jpg');
                background-size: cover;
                background-position: center;
                z-index: 100; /* TOP LAYER */
                background-color: #58D68D;
            }
            
            /* Cover Slide Content */
            .cover-container {
                position: absolute;
                bottom: 150px; 
                left: 68px;
                right: 68px;
                z-index: 10;
                padding: 0;
            }
            .cover-title {
                color: #FFFFFF;
                font-weight: 800;
                text-transform: uppercase;
                line-height: 0.98;
                letter-spacing: -2.8px;
                margin: 0 0 22px 0;
                max-width: 860px;
                text-shadow: 0 3px 14px rgba(0,0,0,0.34);
            }
            .cover-title .tease {
                display: block;
                font-size: 0.52em;
                letter-spacing: -1.4px;
                opacity: 0.98;
                margin-bottom: 14px;
            }
            .cover-title .punch {
                display: block;
            }
            .cover-tap {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: 700;
                opacity: 0.95;
                letter-spacing: 0.2px;
                text-transform: uppercase;
            }

            /* Content Slide Card */
            .card {
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                width: 920px;
                height: 1050px;
                background: linear-gradient(180deg, rgba(9, 12, 18, 0.74) 0%, rgba(9, 12, 18, 0.84) 100%);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 40px;
                padding: 100px 80px 80px 80px;
                z-index: 20;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.28);
                backdrop-filter: blur(28px) saturate(1.08);
            }
            
            .slide-header {
                font-size: 44px;
                font-weight: 800;
                text-transform: uppercase;
                margin: 0 0 25px 0;
                line-height: 1.3;
            }
            .slide-header.blue { color: #5DADE2; }
            .slide-header.mint { color: #58D68D; }
            .slide-header.purple { color: #C39BD3; }
            
            .slide-body {
                font-size: 34px;
                font-weight: 400;
                color: #FFFFFF;
                line-height: {body_line_height};
                flex-grow: 0;
                margin-bottom: 20px;
                text-shadow: 0 2px 10px rgba(0,0,0,0.18);
            }
            .slide-body b {
                font-weight: 800;
                color: #FFFFFF;
                text-shadow: 0 0 10px rgba(255,255,255,0.3);
            }
            
            .slide-fraction {
                text-align: center;
                font-size: 30px;
                color: #8B949E;
                font-weight: 600;
                margin-top: 40px;
            }
            
            /* CTA Slide */
            .cta-title {
                font-size: 70px;
                font-weight: 800;
                color: #FFFFFF;
                margin: 0 0 30px 0;
                line-height: 1.2;
            }
            .cta-subtitle {
                font-size: 40px;
                color: #8B949E;
                margin: 0 0 100px 0;
            }
            .cta-button {
                background-color: #00C853;
                color: #FFFFFF;
                font-size: 45px;
                font-weight: 700;
                padding: 35px 80px;
                border-radius: 20px;
                display: inline-block;
                text-align: center;
                width: max-content;
            }

        </style>
    </head>
    <body>
        {body_content}
    </body>
    </html>
    """
    
    # Calculate title font size based on length
    title_raw = sanitize_display_text(slides_data.get('cover', 'MEDICAL BREAKTHROUGH'))
    title_lines = [line.strip() for line in title_raw.replace('\\n', '\n').split('\n') if line.strip()]
    if len(title_lines) < 2:
        title_lines = [title_lines[0] if title_lines else "MEDICAL", "BREAKTHROUGH"]
    title = f'<span class="tease">{title_lines[0]}</span><span class="punch">{title_lines[1]}</span>'
    
    t_len = len(title_raw)
    if t_len < 18:
        t_size = 138
    elif t_len < 24:
        t_size = 128
    elif t_len < 32:
        t_size = 116
    elif t_len < 40:
        t_size = 102
    else:
        t_size = 92
        
    line_height = "52px"

    def get_base64_image(image_path_or_url):
        if not image_path_or_url:
            return None
        
        # Round 53: Always download remote URLs first to ensure full offline rendering reliability
        target_path = image_path_or_url
        is_temp = False
        
        if image_path_or_url.startswith("http"):
            try:
                print(f"DEBUG: Localizing remote asset for Base64 encoding: {image_path_or_url[:50]}...")
                temp_name = f"render_tmp_{int(time.time() * 1000)}.jpg"
                target_path = os.path.join(base_dir, temp_name)
                response = requests.get(image_path_or_url, timeout=15)
                if response.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(response.content)
                    is_temp = True
                else:
                    return image_path_or_url # Fallback to URL if download fails
            except Exception as e:
                print(f"Warning: Failed to localize {image_path_or_url}: {e}")
                return image_path_or_url
            
        try:
            abs_path = os.path.abspath(target_path)
            if os.path.exists(abs_path):
                ext = abs_path.split('.')[-1].lower()
                mime = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
                with open(abs_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    result = f"data:{mime};base64,{encoded_string}"
                    # Cleanup temp file if created
                    if is_temp:
                        try: os.remove(abs_path)
                        except: pass
                    return result
        except Exception as e:
            print(f"Warning: Base64 conversion failed for {target_path}: {e}")
            
        return None

    bg_image_embed = get_base64_image(bg_image_url)
    bg_image_html = f'<img src="{bg_image_embed}">' if bg_image_embed else ""
    bg_soft_html = f'<div class="bg-soft"><img src="{bg_image_embed}"></div>' if bg_image_embed else ""
    
    # Pre-check if logo.jpg exists
    logo_file = os.path.join(base_dir, 'logo.jpg')
    if not os.path.exists(logo_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_file = os.path.join(script_dir, 'logo.jpg')
    
    logo_embed = get_base64_image(logo_file) if os.path.exists(logo_file) else logo_path
        
    logo_html = f"""<div class="logo" style="background-image: url('{logo_embed}');"></div>"""

    slides_html = []
    
    # 1. Cover
    cover_cta = sanitize_display_text(slides_data.get('cover_cta', 'Tap to learn more'))
    cover_cta = cover_cta.replace('➔', '').replace('⬇️', '').replace('âž”', '').strip().upper()
    cover_body = f"""
    <div class="bg-layer">{bg_image_html}</div>
    <div class="cover-overlay"></div>
    {logo_html}
    <div class="cover-container">
        <h1 class="cover-title" style="font-size: {t_size}px;">{title}</h1>
        <div class="cover-tap">{cover_cta}</div>
    </div>
    """
    
    html = html_template.replace('{body_content}', cover_body).replace('{body_line_height}', line_height)
    slides_html.append(html)
    
    # Helper for content slides
    def make_content_slide(stitle, sbody, fraction, color):
        stitle = sanitize_display_text(stitle)
        sbody = sanitize_display_text(sbody)
        content = f"""
        {bg_soft_html}
        <div class="bg-layer">{bg_image_html}</div>
        <div class="overlay"></div>
        {logo_html}
        <div class="card">
            <div class="slide-header {color}">{stitle}</div>
            <div class="slide-body">{sbody}</div>
            <div class="slide-fraction">{fraction}</div>
        </div>
        """
        return html_template.replace('{body_content}', content).replace('{body_line_height}', line_height)
        
    # 2. Content Slide 1
    slides_html.append(make_content_slide(
        slides_data.get('slide_1_title', 'THE BREAKTHROUGH'), 
        slides_data.get('slide_1_body', ''), 
        "2/4", "blue"
    ))

    # 3. Content Slide 2
    slides_html.append(make_content_slide(
        slides_data.get('slide_2_title', 'THE IMPACT'), 
        slides_data.get('slide_2_body', ''), 
        "3/4", "mint"
    ))
    
    # 4. CTA Slide
    cta_question = sanitize_display_text(slides_data.get('slide_4_question', 'Would you try this treatment?'))
    cta_content = f"""
    {bg_soft_html}
    <div class="bg-layer">{bg_image_html}</div>
    <div class="overlay"></div>
    {logo_html}
    <div class="card" style="justify-content: space-between; padding: 96px 78px 70px; text-align: center; height: 980px;">
        <div>
            <div class="cta-title" style="font-size: 58px; margin-bottom: 48px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 34px;">{cta_question}</div>
            <div class="cta-subtitle" style="font-size: 42px; color: #FFFFFF; font-weight: 700; margin-bottom: 8px;">Stay informed daily</div>
            <div class="cta-subtitle" style="font-size: 34px; color: #A7B0BC; margin-bottom: 0;">@medicalnews_daily</div>
        </div>
        <div>
        <div class="cta-button" style="margin: 0 auto;">Follow for more</div>
            <div class="slide-fraction">4/4</div>
        </div>
    </div>
    """
    slides_html.append(html_template.replace('{body_content}', cta_content).replace('{body_line_height}', line_height))
    
    return slides_html

def parse_slide_content(slide_text):
    """Splits 'TITLE: Body' if title is provided, else returns default Title and body."""
    if ":" in slide_text and len(slide_text.split(":")[0]) < 40:
        parts = slide_text.split(":", 1)
        return parts[0].strip().upper(), parts[1].strip()
    return "DID YOU KNOW?", slide_text

def generate_carousel_images(slides_data, bg_image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    slides_html = generate_html(slides_data, bg_image_path, output_dir)
    image_paths = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
        
        for i, html_str in enumerate(slides_html):
            temp_html = os.path.join(output_dir, f"temp_{i}.html")
            with open(temp_html, "w", encoding='utf-8') as f:
                f.write(html_str)
                
            page.goto(f"file://{os.path.abspath(temp_html)}", wait_until="load")
            page.wait_for_timeout(500) # Ensure fonts and filters load
            
            unique_suffix = int(time.time() * 100)
            output_path = os.path.join(output_dir, f"slide_{unique_suffix}_{i+1}.jpg")
            page.screenshot(path=output_path, type="jpeg", quality=90)
            image_paths.append(output_path)
            
            # Clean up temp html
            try:
                os.remove(temp_html)
            except:
                pass
                
        browser.close()
        
    return image_paths

if __name__ == "__main__":
    # Test generator
    mock_data = {
        "cover": "CELL'S SECRET ENGINE UNLOCKED: CANCER'S NEW ENEMY?",
        "slide_1": "JUST DISCOVERED: Imagine finding a whole new factory running inside something you thought you knew inside out. Scientists just did that, deep within our cells.",
        "slide_2": "HOW YOUR DNA GETS REPAIRED: These newly found enzymes aren't just lounging around. They form unique patterns, like fingerprints, in different body tissues and even in cancers.",
        "slide_3": "THE FUTURE OF CANCER FIGHTING: This breakthrough reveals an unexpected direct connection between a cell's energy system and how our genes are controlled.",
        "caption": "Test."
    }
    
    # Create dummy bg image
    base = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(base, "media")
    os.makedirs(media_dir, exist_ok=True)
    dummy_bg = os.path.join(media_dir, "cover.png")
    if not os.path.exists(dummy_bg):
        # Just download a random unsplash image
        import urllib.request
        print("Downloading placeholder background...")
        urllib.request.urlretrieve("https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop", dummy_bg)
        
    print("Generating images...")
    images = generate_carousel_images(mock_data, dummy_bg, media_dir)
    print(f"Generated: {images}")
