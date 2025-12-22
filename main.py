import os
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
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
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
# Dashboard
# --------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# --------------------
# Platform pages
# --------------------
@app.route("/platform/<name>")
def platform(name):
    return render_template(f"{name}.html")

# --------------------
# Community feed / posts
# --------------------
# Temporary in-memory posts for testing
POSTS = []

@app.route("/feed")
def feed():
    return render_template("feed.html", posts=POSTS)

@app.route("/post", methods=["GET", "POST"])
def post():
    saved = []  # TEMP saved ideas
    if request.method == "POST":
        content = request.form.get("content")
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        attached_idea = request.form.get("attached_idea")
        POSTS.append({
            "user": {"username": session.get("user")},
            "content": content,
            "image": filename,
            "attached_idea": attached_idea,
            "likes": [],
            "timestamp": "Just now"
        })
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved)

# --------------------
# Serve uploaded files
# --------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# Tools API
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print(data)
    return jsonify({"status": "success"})

# --------------------
# Catch-all 404
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --------------------
# Run locally
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
