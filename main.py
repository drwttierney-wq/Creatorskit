import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort, flash
from database import db, User, Post, Message, followers
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from ai_engine import generate_hashtags  # Add more tool imports as needed

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

app.debug = False

# Persistent uploads on disk
UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Persistent DB on disk
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
        if username and password:
            if User.query.filter_by(username=username).first():
                flash("Username already taken")
            else:
                hashed = generate_password_hash(password)
                new_user = User(username=username, password=hashed)
                db.session.add(new_user)
                db.session.commit()
                flash("Registered successfully — login now")
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
        flash("Invalid credentials")
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
    if name.lower() in ['tiktok', 'youtube', 'instagram', 'twitter', 'facebook', 'snapchat', 'reddit', 'threads', 'twitch', 'pinterest', 'linkedin', 'discord', 'onlyfans', 'monetization']:
        return render_template(name.lower() + '.html')
    abort(404)

@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    tool = request.form.get("tool")
    input_text = request.form.get("input")
    if tool == "hashtag":
        hashtags = generate_hashtags(input_text)
        return jsonify({"hashtags": hashtags})
    # Add more tools here, e.g., for other platforms
    return jsonify({"error": "Tool not found"})

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
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
        if content and content.strip():
            new_post = Post(user_id=session["user_id"], content=content.strip(), image_path=image_path)
            db.session.add(new_post)
            db.session.commit()
            flash("Post created!")
            return redirect(url_for("community"))
    return render_template("post.html")

@app.route("/like_post/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
    return redirect(url_for("community"))

@app.route("/messages")
@login_required
def messages():
    conversations = db.session.query(User).join(Message, User.id == Message.sender_id).filter(Message.receiver_id == session["user_id"]).group_by(User.id).all()
    return render_template("messages_inbox.html", conversations=conversations)

@app.route("/chat/<username>", methods=["GET", "POST"])
@login_required
def chat(username):
    other_user = User.query.filter_by(username=username).first()
    if not other_user:
        abort(404)
    if request.method == "POST":
        content = request.form.get("content")
        if content and content.strip():
            new_message = Message(sender_id=session["user_id"], receiver_id=other_user.id, content=content.strip())
            db.session.add(new_message)
            db.session.commit()
        return redirect(url_for("chat", username=username))
    messages = Message.query.filter(
        ((Message.sender_id == session["user_id"]) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == session["user_id"]))
    ).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", other_user=other_user, messages=messages)

@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    current_user = User.query.get(session["user_id"])
    is_following = current_user.followed.filter_by(id=user.id).first() is not None
    return render_template("profile.html", user=user, posts=posts, is_following=is_following)

@app.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user and user.id != session["user_id"]:
        current_user = User.query.get(session["user_id"])
        current_user.followed.append(user)
        db.session.commit()
    return redirect(url_for("profile", username=username))

@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user = User.query.get(session["user_id"])
        current_user.followed.remove(user)
        db.session.commit()
    return redirect(url_for("profile", username=username))

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        user.bio = request.form.get("bio")
        db.session.commit()
        flash("Settings updated")
    return render_template("settings.html", user=user)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
