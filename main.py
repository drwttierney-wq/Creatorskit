import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from database import get_db, init_db

# --------------------
# Flask App Setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize DB
init_db()

# --------------------
# Dummy Data
# --------------------
PLATFORMS = {
    "tiktok": ["Idea Generator", "Script Writer", "Hashtag Generator", "Caption Creator", "Trend Analyzer", "Sound Finder", "Thumbnail Idea"],
    "youtube": ["Title Generator","Description Writer","Script Writer","Thumbnail Prompt","Tag Generator","Idea Brainstorm","SEO Analyzer"],
    "twitter": ["Thread Writer","Tweet Generator","Reply Ideas","Poll Creator","Quote Tweet","Viral Hook"],
    "facebook": ["Post Creator","Page Manager","Event Planner","Community Insight","Ad Suggestion"],
    "instagram": ["Photo Caption","Story Ideas","Hashtag Finder","Reel Script","Engagement Analyzer","Grid Planner","Collab Ideas"],
    "linkedin": ["Post Writer","Article Generator","Connection Prompt","Job Post Creator","Engagement Tracker","Professional Tips","Networking Ideas"],
    "snapchat": ["Snap Script","AR Filter Ideas","Story Flow","GeoTag Planner","Snap Insights","Trend Tracker","Creative Lens Ideas"],
    "reddit": ["Post Generator","Comment Reply","Title Optimizer","Upvote Strategy","Community Trend","Flair Suggestion","Engagement Tracker"],
    "threads": ["Thread Creator","Reply Ideas","Viral Hook","Conversation Starter","Highlight Picks","Engagement Tracker","Content Scheduler"],
    "twitch": ["Stream Title","Game Trend","Overlay Ideas","Chat Engagement","Subscriber Goals","Content Script","Schedule Planner"],
    "onlyfans": ["Content Planner","Subscriber Message","Promo Strategy","Exclusive Offer","Revenue Tracker","Content Scheduler","Analytics"],
    "discord": ["Server Setup","Role Planner","Bot Ideas","Event Scheduler","Community Poll","Engagement Tracker","Channel Ideas"],
    "monetization": ["Revenue Strategy Planner","Pricing Calculator","Sponsorship Pitch Script","Product Idea Generator","Upsell & Funnel Builder","Affiliate Program Suggestions","Tax & Finance Tips"]
}

DUMMY_USERS = [
    {"id": 1, "username": "Alice"},
    {"id": 2, "username": "Bob"},
    {"id": 3, "username": "Charlie"}
]

DUMMY_FEED = [
    {"id": 1, "user": {"username": "Alice"}, "content": "Check out my viral video idea!", "image": None, "attached_idea": None, "likes": [], "timestamp": "Dec 23 at 14:00"},
    {"id": 2, "user": {"username": "Bob"}, "content": "Here's a caption tip for TikTok.", "image": None, "attached_idea": None, "likes": [], "timestamp": "Dec 23 at 15:30"},
]

# --------------------
# Routes
# --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            session["user"] = username
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Error: {e}"
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", platforms=PLATFORMS)

@app.route("/platform/<platform>")
def platform(platform):
    tools = PLATFORMS.get(platform, [])
    return render_template("platform.html", platform=platform, tools=tools)

@app.route("/feed")
def feed():
    return render_template("feed.html", posts=DUMMY_FEED)

@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "POST":
        content = request.form.get("content")
        attached_idea = request.form.get("attached_idea")
        # save to dummy feed for now
        DUMMY_FEED.append({"id": len(DUMMY_FEED)+1, "user":{"username":session.get("user","Anon")}, "content": content, "image": None, "attached_idea": attached_idea, "likes": [], "timestamp":"Now"})
        return redirect(url_for("feed"))
    return render_template("post.html", saved=[])

@app.route("/messages")
def messages():
    return render_template("messages_inbox.html", users=DUMMY_USERS)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print(data)
    return jsonify({"status": "success"})

# --------------------
# Error Pages
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --------------------
# Run Local
# --------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
