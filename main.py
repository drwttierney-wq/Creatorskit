import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# Init DB
init_db()

# --------------------
# BASIC PAGES
# --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("username")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            session["user"] = username
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Error: {e}"
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/platform/<name>")
def platform(name):
    return render_template(f"{name}.html")

@app.route("/feed")
def feed():
    return render_template("feed.html", posts=[])

@app.route("/post")
def post():
    return render_template("post.html", saved=[])

@app.route("/messages")
def messages():
    return render_template("messages_inbox.html", users=[])

@app.route("/use_tool", methods=["POST"])
def use_tool():
    return jsonify({"status": "success"})

# --------------------
# ERRORS
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
