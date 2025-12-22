import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from database import get_db, init_db
from flask_socketio import SocketIO

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# Ensure database is initialized
init_db()

# Uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# SocketIO
# --------------------
socketio_app = SocketIO(app, async_mode="eventlet")

# --------------------
# BASIC PAGES
# --------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # TEMP login (no password check yet)
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            session["user"] = username
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Error: {e}"
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# --------------------
# Platform Pages
# --------------------
@app.route("/platform/<name>")
def platform(name):
    return render_template(f"{name}.html")


# --------------------
# Feed & Posts
# --------------------
@app.route("/feed")
def feed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")  # TEMP: no posts table yet
    users = cursor.fetchall()
    return render_template("feed.html", posts=users)


@app.route("/post", methods=["GET", "POST"])
def post():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")  # TEMP saved ideas
    saved = cursor.fetchall()
    if request.method == "POST":
        content = request.form.get("content")
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        attached_idea = request.form.get("attached_idea")
        # TEMP: just redirect to feed
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved)


# --------------------
# Messages Inbox
# --------------------
@app.route("/messages")
def messages_inbox():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")  # TEMP
    users = cursor.fetchall()
    return render_template("messages_inbox.html", users=users)


# --------------------
# Serve uploaded files
# --------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# --------------------
# Tool usage API
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print(data)
    return jsonify({"status": "success"})


# --------------------
# SocketIO: Community chat
# --------------------
@socketio_app.on("join_community")
def join_community():
    print("User joined community")


@socketio_app.on("send_message")
def handle_message(data):
    msg = data.get("msg")
    socketio_app.emit("new_message", {"user": session.get("user", "Anon"), "msg": msg})


# --------------------
# 404 Page
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# --------------------
# Run locally / Render
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio_app.run(app, host="0.0.0.0", port=port, debug=True)
