import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort
from database import db, User, Post
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///creatorskit.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --------------------
# ROUTES
# --------------------

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            return "User exists", 400
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/dashboard")
@login_required
def dashboard():
    tools = [
        {"name": "TikTok", "emoji": "🎵", "route": "tiktok", "desc": "Viral videos & trends"},
        {"name": "YouTube", "emoji": "📺", "route": "youtube", "desc": "Growth & monetization"},
        {"name": "Instagram", "emoji": "📸", "route": "instagram", "desc": "Reels & aesthetics"},
        {"name": "Twitter / X", "emoji": "🐦", "route": "twitter", "desc": "Threads & reach"},
        {"name": "Facebook", "emoji": "👥", "route": "facebook", "desc": "Groups & engagement"},
        {"name": "Snapchat", "emoji": "👻", "route": "snapchat", "desc": "Stories & Spotlight"},
        {"name": "Reddit", "emoji": "👽", "route": "reddit", "desc": "Upvotes & discussions"},
        {"name": "Threads", "emoji": "🧵", "route": "threads", "desc": "Conversation starters"},
        {"name": "Twitch", "emoji": "🎮", "route": "twitch", "desc": "Streaming growth"},
        {"name": "Pinterest", "emoji": "📌", "route": "pinterest", "desc": "Discovery & traffic"},
        {"name": "LinkedIn", "emoji": "💼", "route": "linkedin", "desc": "Professional reach"},
        {"name": "Discord", "emoji": "💬", "route": "discord", "desc": "Community building"},
        {"name": "OnlyFans", "emoji": "🔒", "route": "onlyfans", "desc": "Creator monetization"},
        {"name": "Monetization", "emoji": "💰", "route": "monetization", "desc": "Revenue & strategy"}
    ]
    return render_template("dashboard.html", tools=tools)

@app.route("/community")
@login_required
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/messages")
@login_required
def messages():
    return render_template("messages_inbox.html")

@app.route("/post", methods=["GET", "POST"])
@login_required
def post_page():
    if request.method == "POST":
        content = request.form.get("content")
        file = request.files.get("image")
        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = filename
        if content:
            new_post = Post(user=session["user"], content=content, image_path=image_path)
            db.session.add(new_post)
            db.session.commit()
        return redirect(url_for("community"))
    return render_template("post.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/platform/<name>")
@login_required
def platform(name):
    valid_platforms = [t["route"] for t in [
        {"route": "tiktok"}, {"route": "youtube"}, {"route": "instagram"}, {"route": "twitter"},
        {"route": "facebook"}, {"route": "snapchat"}, {"route": "reddit"}, {"route": "threads"},
        {"route": "twitch"}, {"route": "pinterest"}, {"route": "linkedin"}, {"route": "discord"},
        {"route": "onlyfans"}, {"route": "monetization"}
    ]]
    if name.lower() in valid_platforms:
        return render_template(f"{name.lower()}.html")
    abort(404)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
