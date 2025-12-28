import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from database import db, Post

# --------------------
# APP SETUP
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

app.debug = False

# --------------------
# UPLOADS
# --------------------
UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------
# DATABASE
# --------------------
DATABASE_PATH = "/data/database.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --------------------
# AUTH DECORATOR
# --------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --------------------
# PUBLIC ROUTES
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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# --------------------
# CORE APP ROUTES
# --------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/messages")
@login_required
def messages():
    return render_template("inbox.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

# --------------------
# PLATFORM ROUTES
# --------------------
@app.route("/platform/<name>")
@login_required
def platform(name):
    platforms = {
        "tiktok", "youtube", "instagram", "twitter",
        "facebook", "snapchat", "reddit", "threads",
        "twitch", "pinterest", "linkedin", "discord",
        "onlyfans", "monetization"
    }

    if name.lower() in platforms:
        return render_template(f"{name.lower()}.html")

    abort(404)

# --------------------
# COMMUNITY / POSTS
# --------------------
@app.route("/community")
@login_required
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

@app.route("/post")
@login_required
def post_page():
    return render_template("post.html")

@app.route("/create_post", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content")
    image_path = None

    if "image" in request.files:
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename

    if content and content.strip():
        new_post = Post(
            user=session["user"],
            content=content.strip(),
            image_path=image_path
        )
        db.session.add(new_post)
        db.session.commit()

    return redirect(url_for("community"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# ERROR HANDLING
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
