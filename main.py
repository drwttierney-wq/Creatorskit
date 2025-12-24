import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, jsonify, flash, abort
)
from database import db, Post  # Import Post model

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

# IMPORTANT: Disable debug in production
app.debug = False

# Uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Database setup - better for Render persistence
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(INSTANCE_DIR, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()  # Creates tables including Post

# --------------------
# Helper: Login Required
# --------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

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
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Username required")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# Platform routes
PLATFORMS = {
    "tiktok": "tiktok.html",
    "youtube": "youtube.html",
    "instagram": "instagram.html",
    "twitter": "twitter.html",
    "facebook": "facebook.html",
    "snapchat": "snapchat.html",
    "reddit": "reddit.html",
    "threads": "threads.html",
    "twitch": "twitch.html",
    "pinterest": "pinterest.html",
    "linkedin": "linkedin.html",
    "discord": "discord.html",
    "onlyfans": "onlyfans.html",
    "monetization": "monetization.html",
}

@app.route("/platform/<name>")
@login_required
def platform(name):
    template = PLATFORMS.get(name.lower())
    if template and os.path.exists(os.path.join("templates", template)):
        return render_template(template)
    abort(404)

# Community Feed - Real posts
@app.route("/community")
@login_required
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

# Create Post page
@app.route("/post")
@login_required
def post_page():
    return render_template("post.html")

# Handle new post
@app.route("/create_post", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content")
    if content and content.strip():
        new_post = Post(user=session["user"], content=content.strip())
        db.session.add(new_post)
        db.session.commit()
    return redirect("/community")

# Like a post
@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return redirect("/community")

# Messages (placeholder)
@app.route("/messages")
@login_required
def messages():
    return render_template("messages_inbox.html")

# Use tool (AI generation)
@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    data = request.get_json() or {}
    tool = data.get("tool")
    input_text = data.get("input", "").strip()

    if not input_text:
        return jsonify({"status": "error", "message": "No input provided"})

    try:
        if tool == "hashtag":
            words = input_text.lower().split()[:5]
            base = ["fyp", "viral", "trending", "foryou", "explore", "tiktok"]
            variants = [word + str(i) for word in words for i in ["", "1", "2", "official"]]
            all_tags = base + words + variants + [input_text.replace(" ", "")]
            unique = []
            for tag in all_tags:
                if tag not in unique:
                    unique.append(tag)
            hashtags = [f"#{tag}" for tag in unique[:30]]
            return jsonify({
                "status": "success",
                "result": {"hashtags": hashtags}
            })

        return jsonify({
            "status": "success",
            "result": {"text": f"Generated {tool} for: {input_text} (real AI coming soon!)"}
        })

    except Exception as e:
        return jsonify({"status": "error", "message": "Something went wrong"})

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# Error Handling
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("404.html"), 500

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
