import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, jsonify, abort
)
from database import db, Post
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

app.debug = False

UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

DATABASE_PATH = "/data/database.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

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

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

PLATFORMS = {
    "tiktok": "platforms/tiktok.html",
    "youtube": "platforms/youtube.html",
    "instagram": "platforms/instagram.html",
    "twitter": "platforms/twitter.html",
    "facebook": "platforms/facebook.html",
    "snapchat": "platforms/snapchat.html",
    "reddit": "platforms/reddit.html",
    "threads": "platforms/threads.html",
    "twitch": "platforms/twitch.html",
    "pinterest": "platforms/pinterest.html",
    "linkedin": "platforms/linkedin.html",
    "discord": "platforms/discord.html",
    "onlyfans": "platforms/onlyfans.html",
    "monetization": "platforms/monetization.html",
}

@app.route("/platform/<name>")
@login_required
def platform(name):
    template = PLATFORMS.get(name.lower())
    if template:
        return render_template(template)
    abort(404)

@app.route("/community")
@login_required
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

@app.route("/post", methods=["GET", "POST"])
@login_required
def post_page():
    if request.method == "POST":
        content = request.form.get("content")
        image_path = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename

        if content and content.strip():
            new_post = Post(user=session["user"], content=content.strip(), image_path=image_path)
            db.session.add(new_post)
            db.session.commit()
            return redirect("/community")
    return render_template("post.html")

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
            unique = list(dict.fromkeys(all_tags))[:30]
            hashtags = [f"#{tag}" for tag in unique]
            return jsonify({
                "status": "success",
                "result": {"hashtags": hashtags}
            })

        return jsonify({
            "status": "success",
            "result": {"text": f"Generated {tool} for: {input_text}"}
        })

    except Exception as e:
        return jsonify({"status": "error", "message": "Something went wrong"})

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("404.html"), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
