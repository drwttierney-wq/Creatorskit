from flask import request, redirect, url_for, session
from database import init_db, get_dbfrom flask import Flask, render_template, abort

app = Flask(__name__)app.secret_key = "change_this_later"
init_db()

PLATFORMS = {
    "tiktok": {
        "name": "TikTok",
        "color": "#ff0050",
        "description": "Short-form viral content engine"
    },
    "instagram": {
        "name": "Instagram",
        "color": "#C13584",
        "description": "Reels, stories & growth tools"
    },
    "youtube": {
        "name": "YouTube",
        "color": "#FF0000",
        "description": "Long-form & Shorts domination"
    },
    "twitter": {
        "name": "X (Twitter)",
        "color": "#1DA1F2",
        "description": "Threads, reach & engagement"
    },
    "linkedin": {
        "name": "LinkedIn",
        "color": "#0A66C2",
        "description": "Professional growth & authority"
    },
    "snapchat": {
        "name": "Snapchat",
        "color": "#FFFC00",
        "description": "Spotlight & story reach"
    },
    "twitch": {
        "name": "Twitch",
        "color": "#9146FF",
        "description": "Live streaming growth"
    }
}

@app.route("/")
def home():
    return render_template("platform.html", platform="tiktok", data=PLATFORMS["tiktok"])

@app.route("/platform/<platform>")
def platform_page(platform):
    if platform not in PLATFORMS:
        abort(404)
    return render_template(
        "platform.html",
        platform=platform,
        data=PLATFORMS[platform]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
