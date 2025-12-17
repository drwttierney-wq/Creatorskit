import os
import requests

API_KEY = os.getenv("OPENAI_API_KEY")

def ai(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data
    )

    return r.json()["choices"][0]["message"]["content"]

def viral_hooks(niche):
    return ai(f"Generate 5 viral TikTok hooks for niche: {niche}")

def captions(niche):
    return ai(f"Generate 5 high converting captions for {niche}")

def hashtags(niche):
    return ai(f"Generate viral hashtags for {niche}")

def content_plan(niche):
    return ai(f"Create a 7-day viral content plan for {niche}")
