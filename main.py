from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from database import get_db, init_db
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# --------------------
# App Setup
# --------------------
app = Flask(__name__)
app.secret_key = "creators-kit-secret"

# Upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize database
init_db()

# --------------------
# Helpers
# --------------------
def current_user():
    return session.get("user")  # simple session-based auth

# --------------------
# Routes
# --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            session["user"] = username
            return redirect("/dashboard")
        except:
            return "Username taken", 400
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if not current_user():
        return redirect("/login")
    return render_template("dashboard.html")

# --------------------
# Tool Pages
# --------------------
@app.route("/platform/<platform>")
def platform_page(platform):
    if not current_user():
        return redirect("/login")
    # Render toolkit HTML (assumes templates are named like platform.html)
    try:
        return render_template(f"{platform}.html")
    except:
        return "Platform not found", 404

# --------------------
# Save Tool Content
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    platform = data.get("platform")
    tool = data.get("tool")
    content = data.get("content")
    save = data.get("save", False)

    if save:
        db = get_db()
        db.execute(
            "CREATE TABLE IF NOT EXISTS saved_tools (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, platform TEXT, tool_name TEXT, result TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        db.execute(
            "INSERT INTO saved_tools (user, platform, tool_name, result) VALUES (?, ?, ?, ?)",
            (current_user(), platform, tool, content)
        )
        db.commit()

    return jsonify({"status": "success"})

# --------------------
# Feed & Posting
# --------------------
@app.route("/feed")
def feed():
    if not current_user():
        return redirect("/login")
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            image TEXT,
            attached_idea TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    posts = db.execute("SELECT * FROM posts ORDER BY timestamp DESC").fetchall()
    return render_template("feed.html", posts=posts)

@app.route("/post", methods=["GET", "POST"])
def post():
    if not current_user():
        return redirect("/login")
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            image TEXT,
            attached_idea TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    saved = db.execute("SELECT * FROM saved_tools WHERE user=?", (current_user(),)).fetchall()
    
    if request.method == "POST":
        content_text = request.form.get("content")
        attached_idea = request.form.get("attached_idea")
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        db.execute(
            "INSERT INTO posts (user, content, image, attached_idea) VALUES (?, ?, ?, ?)",
            (current_user(), content_text, filename, attached_idea)
        )
        db.commit()
        return redirect("/feed")
    return render_template("post.html", saved=saved)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# Messages
# --------------------
@app.route("/messages")
def messages():
    if not current_user():
        return redirect("/login")
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            content TEXT,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    users = db.execute("SELECT username FROM users WHERE username != ?", (current_user(),)).fetchall()
    return render_template("messages.html", users=users)

@app.route("/messages/<user_id>", methods=["GET", "POST"])
def chat(user_id):
    if not current_user():
        return redirect("/login")
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            content TEXT,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    receiver = db.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    if not receiver:
        return "User not found", 404
    if request.method == "POST":
        content_text = request.form.get("content")
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        db.execute(
            "INSERT INTO messages (sender, receiver, content, image) VALUES (?, ?, ?, ?)",
            (current_user(), receiver["username"], content_text, filename)
        )
        db.commit()
    messages = db.execute(
        "SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC",
        (current_user(), receiver["username"], receiver["username"], current_user())
    ).fetchall()
    return render_template("chat.html", messages=messages, other_user=receiver)

# --------------------
# Community Feed
# --------------------
@app.route("/community")
def community():
    if not current_user():
        return redirect("/login")
    return render_template("community.html")

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
