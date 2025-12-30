import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

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
# IMPORT MODELS
# ----------------------------
from models import User, Post, Comment, Like, Follow, Notification, Conversation, Message

with app.app_context():
    db.create_all()

# ----------------------------
# LOGIN DECORATOR
# ----------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# AUTH ROUTES
# ----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists", "error")
                return redirect(url_for("signup"))
            hashed_pw = generate_password_hash(password)
            user = User(username=username, avatar="default-avatar.png")
            user.password_hash = hashed_pw
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid username or password", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))

# ----------------------------
# INDEX / DASHBOARD
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# ----------------------------
# PLATFORM ROUTES
# ----------------------------
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
# COMMUNITY / POSTS
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
    attached_idea = request.form.get("attached_idea")
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename
    if content:
        post = Post(user_id=session["user_id"], content=content, image=image_path, attached_idea=attached_idea)
        db.session.add(post)
        db.session.commit()
    return redirect(url_for("community"))

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = session["user_id"]
    existing_like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        like = Like(user_id=user_id, post_id=post_id)
        db.session.add(like)
        # Add notification
        if post.user_id != user_id:
            notif = Notification(user_id=post.user_id, type="like", from_user_id=user_id, post_id=post.id)
            db.session.add(notif)
    db.session.commit()
    return redirect(url_for("community"))

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get("comment")
    if content:
        comment = Comment(user_id=session["user_id"], post_id=post.id, content=content)
        db.session.add(comment)
        # Add notification
        if post.user_id != session["user_id"]:
            notif = Notification(user_id=post.user_id, type="comment", from_user_id=session["user_id"], post_id=post.id)
            db.session.add(notif)
        db.session.commit()
    return redirect(url_for("community"))

# ----------------------------
# MESSAGING
# ----------------------------
@app.route("/messages")
@login_required
def messages():
    user_id = session["user_id"]
    conversations = Conversation.query.filter(
        (Conversation.participant1_id == user_id) | (Conversation.participant2_id == user_id)
    ).order_by(Conversation.created_at.desc()).all()
    return render_template("messages_inbox.html", conversations=conversations, user_id=user_id)

@app.route("/chat/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def chat(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    if session["user_id"] not in [conversation.participant1_id, conversation.participant2_id]:
        return "Unauthorized", 403
    if request.method == "POST":
        content = request.form.get("message")
        if content:
            receiver_id = conversation.participant2_id if session["user_id"] == conversation.participant1_id else conversation.participant1_id
            msg = Message(conversation_id=conversation.id, sender_id=session["user_id"], receiver_id=receiver_id, content=content)
            db.session.add(msg)
            # Add notification
            notif = Notification(user_id=receiver_id, type="message", from_user_id=session["user_id"])
            db.session.add(notif)
            db.session.commit()
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", conversation=conversation, messages=messages, user_id=session["user_id"])

# ----------------------------
# PROFILE / SETTINGS
# ----------------------------
@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id=None):
    if user_id is None:
        user_id = session["user_id"]
    user = User.query.get_or_404(user_id)
    post_count = Post.query.filter_by(user_id=user.id).count()
    follower_count = user.followers.count()
    following_count = user.following.count()
    return render_template("profile.html", user=user, post_count=post_count,
                           follower_count=follower_count, following_count=following_count)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

# ----------------------------
# FOLLOW / UNFOLLOW
# ----------------------------
@app.route("/follow/<int:user_id>")
@login_required
def follow(user_id):
    current_user = session["user_id"]
    if current_user == user_id:
        return redirect(url_for("profile", user_id=user_id))
    existing = Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first()
    if existing:
        db.session.delete(existing)
    else:
        follow = Follow(follower_id=current_user, followed_id=user_id)
        db.session.add(follow)
        notif = Notification(user_id=user_id, type="follow", from_user_id=current_user)
        db.session.add(notif)
    db.session.commit()
    return redirect(url_for("profile", user_id=user_id))

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
