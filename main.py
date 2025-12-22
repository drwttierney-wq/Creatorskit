from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # CHANGE THIS

# Make sure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/social_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------- DATABASE MODELS ------------------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50))
    tool = db.Column(db.String(50))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- LOGIN ------------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created, please login")
            return redirect(url_for("login"))
    return render_template("register.html")

# ------------------- DASHBOARD ------------------- #
@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ------------------- PLATFORM PAGES ------------------- #
platform_pages = ["Facebook","tictok","twitter","instagram","linkedin","snapchat","youtube","pinterest","threads","discord"]
for page in platform_pages:
    def platform_page(page=page):
        return render_template(f"{page}.html")
    app.add_url_rule(f"/{page}", page, login_required(platform_page))

# ------------------- SOCIAL FEATURES ------------------- #
@app.route("/feed")
@login_required
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("feed.html", posts=posts)

@app.route("/community", methods=["GET","POST"])
@login_required
def community():
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            post = CommunityPost(user_id=current_user.id, content=content)
            db.session.add(post)
            db.session.commit()
    posts = CommunityPost.query.order_by(CommunityPost.timestamp.desc()).all()
    return render_template("community.html", posts=posts)

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/user_profile/<int:user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("user_profile.html", user=user)

@app.route("/messages_inbox")
@login_required
def messages_inbox():
    return render_template("messages_inbox.html")

# ------------------- TOOL ACTIONS ------------------- #
@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    data = request.json
    platform = data.get("platform")
    tool = data.get("tool")
    content = data.get("content")
    save = data.get("save", False)
    if save and content:
        post = Post(platform=platform, tool=tool, content=content, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
    return jsonify({"status":"success","content":content})

# ------------------- RUN ------------------- #
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
