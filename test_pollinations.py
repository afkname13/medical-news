import urllib.parse
import requests
import time

prompt = "Ultra-realistic microscopic view of a vibrant human cell nucleus, macro photography, 8k"
clean_prompt = urllib.parse.quote(prompt)
img_url = f"https://pollinations.ai/p/{clean_prompt}?width=1080&height=1350&model=flux&seed={int(time.time())}"

print(f"URL: {img_url}")
response = requests.get(img_url)
print(f"Status Code: {response.status_code}")
print(f"Content Type: {response.headers.get('Content-Type')}")
with open("test.jpg", "wb") as f:
    f.write(response.content)
print("Saved to test.jpg")
