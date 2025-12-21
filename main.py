from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from datetime import datetime

# -------------------- SETUP --------------------

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///creatorskit.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# -------------------- MODELS --------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- AUTH --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"])
        user = User(username=request.form["username"], password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# -------------------- PLATFORM ROUTES --------------------
# THESE FIX YOUR ERRORS 🔥

@app.route("/tiktok")
@login_required
def tiktok():
    return render_template("tictok.html")

@app.route("/instagram")
@login_required
def instagram():
    return render_template("instagram.html")

@app.route("/youtube")
@login_required
def youtube():
    return render_template("youtube.html")

@app.route("/twitter")
@login_required
def twitter():
    return render_template("twitter.html")

@app.route("/facebook")
@login_required
def facebook():
    return render_template("Facebook.html")

@app.route("/linkedin")
@login_required
def linkedin():
    return render_template("linkedin.html")

@app.route("/threads")
@login_required
def threads():
    return render_template("threads.html")

@app.route("/reddit")
@login_required
def reddit():
    return render_template("reddit.html")

@app.route("/discord")
@login_required
def discord():
    return render_template("discord.html")

@app.route("/snapchat")
@login_required
def snapchat():
    return render_template("snapchat.html")

@app.route("/pinterest")
@login_required
def pinterest():
    return render_template("pinterest.html")

@app.route("/twitch")
@login_required
def twitch():
    return render_template("twitch.html")

@app.route("/onlyfans")
@login_required
def onlyfans():
    return render_template("onlyfans.html")

@app.route("/monetization")
@login_required
def monetization():
    return render_template("monetization.html")

# -------------------- GUNICORN ENTRY --------------------

application = app
