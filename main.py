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
# Static uploads folder
# --------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# Home / Index
# --------------------
@app.route("/")
def index():
    return render_template("index.html")

# --------------------
# Dashboard
# --------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# --------------------
# Login / Register
# --------------------
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

# --------------------
# Feed
# --------------------
@app.route("/feed")
def feed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("feed.html", posts=users)

# --------------------
# Post new idea
# --------------------
@app.route("/post", methods=["GET", "POST"])
def post():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")  # TEMP saved ideas
    saved = cursor.fetchall()
    if request.method == "POST":
        content = request.form.get("content")
        # Handle image upload
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        attached_idea = request.form.get("attached_idea")
        # TEMP store post (in memory or DB later)
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved)

# --------------------
# Serve uploaded files
# --------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# Social Media Tools
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    # TEMP save / log data
    print(data)
    return jsonify({"status": "success"})

# --------------------
# Catch-all route for 404
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --------------------
# Run with eventlet for SocketIO (Render-friendly)
# --------------------
if __name__ == "__main__":
    import socketio
    from flask_socketio import SocketIO

    socketio_app = SocketIO(app, async_mode="eventlet")
    socketio_app.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
