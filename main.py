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
# Upload folder setup
# --------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# TEMP in-memory storage
# --------------------
posts = []  # Stores community feed posts
users_online = []  # Optional for future chat

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
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
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
            return render_template("register.html", error=f"Error: {e}")
    return render_template("register.html")

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
    template_name = f"{name}.html"
    if not os.path.exists(os.path.join("templates", template_name)):
        return render_template("404.html"), 404
    return render_template(template_name)

# --------------------
# COMMUNITY FEED
# --------------------
@app.route("/feed")
def feed():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("feed.html", posts=posts)

@app.route("/post", methods=["GET", "POST"])
def post():
    if "user" not in session:
        return redirect(url_for("login"))
    saved_ideas = posts  # Show previous posts as "attached ideas"
    if request.method == "POST":
        content = request.form.get("content")
        attached_idea = request.form.get("attached_idea")
        image_file = request.files.get("image")
        filename = None
        if image_file:
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        posts.append({
            "user": {"username": session["user"]},
            "content": content,
            "attached_idea": attached_idea,
            "image": filename
        })
        return redirect(url_for("feed"))
    return render_template("post.html", saved=saved_ideas)

# --------------------
# Serve uploaded files
# --------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# AI TOOL HANDLER
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print("Tool used:", data)
    # Here you can later save to database if needed
    return jsonify({"status": "success"})

# --------------------
# MESSAGES PAGE (Inbox)
# --------------------
@app.route("/messages")
def messages_inbox():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall() if row["username"] != session["user"]]
    return render_template("messages_inbox.html", users=users)

# --------------------
# 404 HANDLER
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
