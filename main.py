import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort, flash, jsonify
from database import db, User, Post, Message, followers
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from ai_engine import generate_hashtags, optimize_caption  # Add more as you build tools

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "prod-key-change-this")

UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Username taken")
        else:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Registered — login now")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user"] = user.username
            return redirect(url_for("dashboard"))
        flash("Invalid login")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
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
    abort(404)

@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    tool = request.form.get("tool")
    input_text = request.form.get("input")
    if tool == "hashtag":
        result = generate_hashtags(input_text)
    elif tool == "caption":
        result = optimize_caption(input_text)
    else:
        result = ["Tool coming soon"]
    return jsonify({"result": result})

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
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_path = filename
        if content:
            post = Post(user_id=session["user_id"], content=content, image_path=image_path)
            db.session.add(post)
            db.session.commit()
            flash("Post created")
            return redirect("/community")
    return render_template("post.html")

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return redirect("/community")

@app.route("/messages")
@login_required
def messages():
    conversations = db.session.query(User).join(Message, User.id == Message.sender_id)\
        .filter(Message.receiver_id == session["user_id"])\
        .group_by(User.id).all()
    return render_template("messages_inbox.html", conversations=conversations)

@app.route("/chat/<username>", methods=["GET", "POST"])
@login_required
def chat(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            msg = Message(sender_id=session["user_id"], receiver_id=other_user.id, content=content)
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("chat", username=username))
    messages = Message.query.filter(
        ((Message.sender_id == session["user_id"]) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == session["user_id"]))
    ).order_by(Message.timestamp).all()
    return render_template("chat.html", other_user=other_user, messages=messages)

@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    current_user = User.query.get(session["user_id"])
    is_following = current_user.followed.filter_by(id=user.id).first() is not None
    return render_template("profile.html", user=user, posts=posts, is_following=is_following)

@app.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    current = User.query.get(session["user_id"])
    if user not in current.followed:
        current.followed.append(user)
        db.session.commit()
    return redirect(url_for("profile", username=username))

@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    current = User.query.get(session["user_id"])
    if user in current.followed:
        current.followed.remove(user)
        db.session.commit()
    return redirect(url_for("profile", username=username))

@app.route("/settings")
@login_required
def settings():
    user = User.query.get(session["user_id"])
    return render_template("settings.html", user=user)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return "Internal Server Error — check logs", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
