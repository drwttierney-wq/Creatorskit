import os
import requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps

# ----------------------------
# APP SETUP
# ----------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-production")

# ----------------------------
# UPLOAD CONFIG
# ----------------------------
UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------
# DATABASE CONFIG
# ----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ----------------------------
# MODELS
# ----------------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    likes = db.relationship("Like", backref="post", lazy=True)
    comments = db.relationship("Comment", backref="post", lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

with app.app_context():
    db.create_all()

# ----------------------------
# LOGIN DECORATOR
# ----------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# AI CORE (REAL AI)
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_openai(system_prompt, user_prompt):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.8,
        },
        timeout=30,
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]

# ----------------------------
# BASIC ROUTES
# ----------------------------
@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ----------------------------
# PLATFORM PAGES
# ----------------------------
@app.route("/platform/<name>")
@login_required
def platform(name):
    valid = [
        "tiktok","youtube","instagram","twitter","facebook","snapchat",
        "reddit","threads","twitch","pinterest","linkedin","discord",
        "onlyfans","monetization"
    ]
    if name.lower() in valid:
        return render_template(f"{name.lower()}.html")
    return "Page not found", 404

# ----------------------------
# COMMUNITY
# ----------------------------
@app.route("/community")
@login_required
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

@app.route("/create_post", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content")
    image_path = None

    if "image" in request.files:
        file = request.files["image"]
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename

    if content:
        post = Post(user=session["user"], content=content, image_path=image_path)
        db.session.add(post)
        db.session.commit()

    return redirect("/community")

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    existing = Like.query.filter_by(
        post_id=post_id, user=session["user"]
    ).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(user=session["user"], post_id=post_id))

    db.session.commit()
    return redirect("/community")

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment_post(post_id):
    content = request.form.get("comment")
    if content:
        db.session.add(
            Comment(user=session["user"], content=content, post_id=post_id)
        )
        db.session.commit()
    return redirect("/community")

# ----------------------------
# PROFILE / MESSAGES
# ----------------------------
@app.route("/messages")
@login_required
def messages():
    return render_template("messages_inbox.html")

@app.route("/profile")
@login_required
def profile():
    post_count = Post.query.filter_by(user=session["user"]).count()
    return render_template(
        "profile.html",
        post_count=post_count,
        follower_count=0,
        following_count=0,
    )

# ----------------------------
# UPLOADS
# ----------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ----------------------------
# 🔥 TIKTOK AI TOOLS (REAL)
# ----------------------------
@app.route("/api/tiktok/hooks", methods=["POST"])
@login_required
def tiktok_hooks():
    topic = request.json.get("topic")
    result = call_openai(
        "You are a TikTok viral hook expert.",
        f"Generate 7 viral TikTok hooks about {topic}",
    )
    return jsonify({"result": result})

@app.route("/api/tiktok/captions", methods=["POST"])
@login_required
def tiktok_captions():
    topic = request.json.get("topic")
    result = call_openai(
        "You are a TikTok caption expert.",
        f"Write 7 high engagement TikTok captions about {topic}",
    )
    return jsonify({"result": result})

@app.route("/api/tiktok/hashtags", methods=["POST"])
@login_required
def tiktok_hashtags():
    topic = request.json.get("topic")
    result = call_openai(
        "You are a TikTok hashtag strategist.",
        f"Generate 20 viral TikTok hashtags for {topic}",
    )
    return jsonify({"result": result})

@app.route("/api/tiktok/script", methods=["POST"])
@login_required
def tiktok_script():
    topic = request.json.get("topic")
    result = call_openai(
        "You are a TikTok script writer.",
        f"Write a 30-second TikTok script about {topic}",
    )
    return jsonify({"result": result})

# ----------------------------
# RUN (LOCAL ONLY)
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
