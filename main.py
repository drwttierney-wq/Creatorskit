import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, jsonify
)
from database import db  # Assuming you have models/init in database.py

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-prod")

# --------------------
# Database setup
# --------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --------------------
# Uploads
# --------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# Helpers
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
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# Platform toolkits (add all your templates here)
PLATFORMS = {
    "tiktok": "tiktok.html",  # Add if you have it, or create
    "instagram": "instagram.html",
    "youtube": "youtube.html",
    "twitter": "twitter.html",
    "facebook": "facebook.html",
    "discord": "discord.html",
    "linkedin": "linkedin.html",
    "onlyfans": "onlyfans.html",
    # Add more as you create templates
}

@app.route("/platform/<platform_name>")
@login_required
def platform(platform_name):
    template = PLATFORMS.get(platform_name.lower())
    if not template:
        return render_template("404.html"), 404
    return render_template(template)

@app.route("/community")
@login_required
def community():
    return render_template("community.html")

@app.route("/feed")
@login_required
def feed():
    return render_template("feed.html")

@app.route("/messages")
@login_required
def messages():
    # Later: pull real users/conversations from DB
    return render_template("messages_inbox.html", users=[])

@app.route("/chat")  # Or /chat/<user_id> later
@login_required
def chat():
    return render_template("chat.html")

@app.route("/monetization")
@login_required
def monetization():
    return render_template("monetization.html")

@app.route("/post")
@login_required
def post():
    return render_template("post.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    data = request.get_json() or {}
    # Later: call ai_engine.py here with data['prompt'] etc.
    # For now, echo back for testing
    result = {"generated": f"Echo: {data.get('input', 'No input')}"}
    return jsonify({"status": "success", "result": result})

# --------------------
# Errors
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
