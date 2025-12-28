import os
from functools import wraps
from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    send_from_directory, abort
)
from werkzeug.utils import secure_filename
from database import db, Post

# --------------------
# APP SETUP
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

app.config["DEBUG"] = False

# --------------------
# DATABASE
# --------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(DATA_DIR, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --------------------
# UPLOADS
# --------------------
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------
# AUTH DECORATOR
# --------------------
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

# --------------------
# PUBLIC ROUTES
# --------------------
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/signup")
def signup():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# --------------------
# APP ROUTES (LOGGED IN)
# --------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

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
    content = request.form.get("content", "").strip()
    image_path = None

    if "image" in request.files:
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = filename

    if content:
        post = Post(
            user=session["user"],
            content=content,
            image_path=image_path
        )
        db.session.add(post)
        db.session.commit()

    return redirect(url_for("community"))

@app.route("/platform/<name>")
@login_required
def platform(name):
    allowed = {
        "tiktok", "youtube", "instagram", "twitter",
        "facebook", "snapchat", "reddit", "threads",
        "twitch", "pinterest", "linkedin", "discord",
        "onlyfans", "monetization"
    }
    name = name.lower()
    if name in allowed:
        return render_template(f"{name}.html")
    abort(404)

# --------------------
# FILES
# --------------------
@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --------------------
# ERRORS
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
