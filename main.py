import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from database import get_db, init_db

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# Ensure database is initialized
init_db()

# --------------------
# Uploads folder
# --------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# BASIC PAGES
# --------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------
# LOGIN & REGISTER
# --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # TEMP login: store username in session
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


# --------------------
# DASHBOARD
# --------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")


# --------------------
# PLATFORM PAGES
# --------------------
@app.route("/platform/<name>")
def platform(name):
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template(f"{name}.html")


# --------------------
# COMMUNITY / POSTS
# --------------------
@app.route("/feed")
def feed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")  # TEMP: just show users
    posts = cursor.fetchall()
    return render_template("feed.html", posts=posts)


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
        # TEMP: store post later
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved)


# --------------------
# MESSAGES
# --------------------
@app.route("/messages")
def messages_inbox():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("messages_inbox.html", users=users)


# --------------------
# UPLOADED FILES
# --------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# --------------------
# AI TOOL ROUTE (TEMP)
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print(data)
    return jsonify({"status": "success"})


# --------------------
# 404 ERROR
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# --------------------
# RUN APP
# --------------------
if __name__ == "__main__":
    from flask_socketio import SocketIO
    socketio_app = SocketIO(app, async_mode="eventlet")
    socketio_app.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
