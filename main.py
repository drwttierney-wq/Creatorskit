import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "change-this-in-production"

UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=db.func.now())

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
    session.clear()  # Keeps landing clean
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

@app.route("/platform/<name>")
@login_required
def platform(name):
    valid = ["tiktok", "youtube", "instagram", "twitter", "facebook", "snapchat", "reddit", "threads", "twitch", "pinterest", "linkedin", "discord", "onlyfans", "monetization"]
    if name.lower() in valid:
        return render_template(f"{name.lower()}.html")
    return "Page not found", 404

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
    if 'image' in request.files:
        file = request.files['image']
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename
    if content:
        post = Post(user=session["user"], content=content, image_path=image_path)
        db.session.add(post)
        db.session.commit()
    return redirect("/community")

@app.route("/messages")
@login_required
def messages():
    return render_template("messages_inbox.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
