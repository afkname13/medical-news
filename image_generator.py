import os
import urllib.parse
from playwright.sync_api import sync_playwright

def generate_html(slides_data, bg_image_url, base_dir):
    """Generates the HTML file for each slide."""
    
    # We will use base64 or raw URLs. Assuming we fetch Unsplash images and save locally.
    # To keep things simple, we'll just reference the local bg image.
    # Ensure bg_image_url is a path or valid string
    if not bg_image_url:
        bg_image_path = "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=1080&auto=format&fit=crop"
    elif bg_image_url.startswith("http"):
        bg_image_path = bg_image_url
    else:
        bg_image_path = f"file://{os.path.abspath(bg_image_url)}"
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
                background-image: url('{bg_image}');
                background-size: cover;
                background-position: center;
                z-index: 1;
            }
            .bg-layer.blurred {
                filter: blur(60px);
                transform: scale(1.1); /* Prevent blur from shrinking edges */
            }
            .overlay {
                position: absolute;
                top: 0; left: 0; width: 1080px; height: 1350px;
                background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.4) 30%, rgba(0,0,0,0) 80%);
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
                left: 80px;
                right: 80px;
                z-index: 10;
            }
            .cover-title {
                color: #FFFFFF;
                font-weight: 800;
                word-wrap: normal;
                word-break: keep-all;
                overflow-wrap: normal;
                text-transform: uppercase;
                line-height: 1.15;
                margin: 0 0 80px 0;
            }
            .cover-tap {
                color: #FFFFFF;
                font-size: 34px;
                font-weight: 700;
                opacity: 0.9;
                letter-spacing: 1px;
            }

            /* Content Slide Card */
            .card {
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                width: 920px;
                height: 1050px;
                background-color: rgba(10, 12, 18, 0.85); /* Slightly darker obsidian */
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 40px;
                padding: 100px 80px 80px 80px;
                z-index: 20;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
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
    title_raw = slides_data.get('cover', 'MEDICAL BREAKTHROUGH')
    title = title_raw.replace('\\n', '<br>').replace('\n', '<br>')
    
    t_len = len(title_raw)
    if t_len < 30:
        t_size = 110
    elif t_len < 50:
        t_size = 90
    else:
        t_size = 80
        
    line_height = "52px"
    
    # Pre-check if logo.jpg exists in base_dir
    logo_file = os.path.join(base_dir, 'logo.jpg')
    if os.path.exists(logo_file):
        logo_url = f"file://{logo_file}"
    else:
        # Check adjacent to this script too
        script_dir = os.path.dirname(os.path.abspath(__file__))
        adj_logo = os.path.join(script_dir, 'logo.jpg')
        if os.path.exists(adj_logo):
            logo_url = f"file://{adj_logo}"
        else:
            logo_url = logo_path
        
    logo_html = f"""<div class="logo" style="background-image: url('{logo_url}');"></div>"""

    slides_html = []
    
    # 1. Cover
    cover_cta = slides_data.get('cover_cta', 'TAP TO LEARN MORE ➔')
    cover_body = f"""
    <div class="bg-layer"></div>
    <div class="overlay"></div>
    {logo_html}
    <div class="cover-container">
        <h1 class="cover-title" style="font-size: {t_size}px;">{title}</h1>
        <div class="cover-tap">{cover_cta}</div>
    </div>
    """
    
    html = html_template.replace('{bg_image}', bg_image_path).replace('{body_content}', cover_body).replace('{body_line_height}', line_height)
    slides_html.append(html)
    
    # Helper for content slides
    def make_content_slide(stitle, sbody, fraction, color):
        content = f"""
        <div class="bg-layer blurred"></div>
        <div class="overlay"></div>
        {logo_html}
        <div class="card">
            <div class="slide-header {color}">{stitle}</div>
            <div class="slide-body">{sbody}</div>
            <div class="slide-fraction">{fraction}</div>
        </div>
        """
        return html_template.replace('{bg_image}', bg_image_path).replace('{body_content}', content).replace('{body_line_height}', line_height)
        
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
    cta_question = slides_data.get('slide_4_question', 'Would you try this treatment?')
    cta_content = f"""
    <div class="bg-layer blurred"></div>
    <div class="overlay"></div>
    {logo_html}
    <div class="card" style="justify-content: center; padding: 120px; text-align: center;">
        <div class="cta-title" style="font-size: 60px; margin-bottom: 60px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 40px;">{cta_question}</div>
        <div class="cta-subtitle" style="font-size: 45px; color: #FFFFFF; font-weight: 700; margin-bottom: 10px;">Stay informed daily</div>
        <div class="cta-subtitle" style="font-size: 35px; color: #8B949E; margin-bottom: 60px;">@medicalnews_daily</div>
        <div class="cta-button" style="margin: 0 auto;">Follow for more</div>
        <div class="slide-fraction">4/4</div>
    </div>
    """
    slides_html.append(html_template.replace('{bg_image}', bg_image_path).replace('{body_content}', cta_content).replace('{body_line_height}', line_height))
    
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
                
            page.goto(f"file://{os.path.abspath(temp_html)}", wait_until="networkidle")
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
