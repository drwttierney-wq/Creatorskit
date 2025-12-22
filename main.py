import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
app = Flask(__name__)
app.secret_key = "creators-kit-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
socketio = SocketIO(app)

# ----------------------
# MODELS
# ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300))
    attached_idea = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('Like', backref='post', lazy=True)
    user = db.relationship('User', backref='posts')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    image = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------
# USER LOADER
# ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# ROUTES
# ----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Username exists!"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ----------------------
# TOOLKIT ROUTES
# ----------------------
tool_platforms = [
    'facebook','instagram','discord','linkedin','onlyfans','pinterest','reddit',
    'snapchat','threads','tiktok','youtube','twitter','twitch','monetization'
]

@app.route("/platform/<platform>")
@login_required
def platform(platform):
    if platform.lower() not in tool_platforms:
        return "Invalid platform"
    template_name = platform.lower() + ".html"
    return render_template(template_name)

@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    data = request.json
    # Here you would normally call ai_engine.py to generate content
    return jsonify({"status": "success"})

# ----------------------
# FEED / POSTS
# ----------------------
@app.route("/feed")
@login_required
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("feed.html", posts=posts, Follow=Follow, current_user=current_user)

@app.route("/post", methods=["GET", "POST"])
@login_required
def post_idea():
    saved = []  # You can implement saved ideas
    if request.method == "POST":
        content = request.form['content']
        attached_idea = request.form.get('attached_idea')
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        post = Post(content=content, attached_idea=attached_idea, image=filename, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved)

@app.route("/uploaded/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return redirect(url_for("feed"))
    existing = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(post_id=post_id, user_id=current_user.id))
    db.session.commit()
    return redirect(url_for("feed"))

@app.route("/follow/<int:user_id>")
@login_required
def follow(user_id):
    if user_id == current_user.id:
        return redirect(url_for("feed"))
    existing = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Follow(follower_id=current_user.id, followed_id=user_id))
    db.session.commit()
    return redirect(request.referrer or url_for("feed"))

# ----------------------
# MESSAGES
# ----------------------
@app.route("/messages")
@login_required
def messages_inbox():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template("messages_inbox.html", users=users)

@app.route("/messages/<int:other_id>", methods=["GET", "POST"])
@login_required
def chat(other_id):
    other_user = User.query.get(other_id)
    if not other_user:
        return redirect(url_for("messages_inbox"))
    if request.method == "POST":
        content = request.form.get('content')
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        msg = Message(sender_id=current_user.id, receiver_id=other_id, content=content, image=filename)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("chat", other_id=other_id))
    messages = Message.query.filter(
        ((Message.sender_id==current_user.id) & (Message.receiver_id==other_id)) |
        ((Message.sender_id==other_id) & (Message.receiver_id==current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", messages=messages, other_user=other_user)

# ----------------------
# COMMUNITY CHAT
# ----------------------
@app.route("/community")
@login_required
def community():
    return render_template("community.html")

@socketio.on("join_community")
def join_community():
    pass  # No server-side room needed for one room

@socketio.on("send_message")
def send_message(data):
    msg = data.get("msg")
    socketio.emit("new_message", {"user": current_user.username, "msg": msg}, broadcast=True)

# ----------------------
# PROFILE
# ----------------------
@app.route("/profile/<int:user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for("dashboard"))
    return render_template("user_profile.html", user=user)

# ----------------------
# INITIALIZE DB
# ----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
