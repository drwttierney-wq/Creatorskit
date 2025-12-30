import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-in-production"

# ----------------------------
# UPLOAD CONFIG
# ----------------------------
UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
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
# ROUTES
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

@app.route("/platform/<name>")
@login_required
def platform(name):
    valid = ["tiktok","youtube","instagram","twitter","facebook","snapchat",
             "reddit","threads","twitch","pinterest","linkedin","discord",
             "onlyfans","monetization"]
    if name.lower() in valid:
        return render_template(f"{name.lower()}.html")
    return "Page not found", 404

# ----------------------------
# COMMUNITY / FEED
# ----------------------------
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

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(post_id=post_id, user=session["user"]).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        like = Like(user=session["user"], post_id=post_id)
        db.session.add(like)
    db.session.commit()
    return redirect("/community")

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get("comment")
    if content:
        comment = Comment(user=session["user"], content=content, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
    return redirect("/community")

# ----------------------------
# MESSAGES / PROFILE / SETTINGS
# ----------------------------
@app.route("/messages")
@login_required
def messages():
    return render_template("messages_inbox.html")

@app.route("/profile")
@login_required
def profile():
    # Example: count stats dynamically
    post_count = Post.query.filter_by(user=session["user"]).count()
    follower_count = 0   # Placeholder if you implement followers table
    following_count = 0  # Placeholder if you implement followers table
    return render_template("profile.html",
                           post_count=post_count,
                           follower_count=follower_count,
                           following_count=following_count)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

# ----------------------------
# UPLOADS
# ----------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
