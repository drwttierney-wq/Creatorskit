import os
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, jsonify, abort
)
from database import db

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# --------------------
# Database setup
# --------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --------------------
# Uploads
# --------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# Helpers
# --------------------
def login_required():
    return "user" in session

# --------------------
# Routes
# --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return redirect(url_for("login"))

        session["user"] = username
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return redirect(url_for("register"))

        session["user"] = username
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Whitelisted platform pages
PLATFORMS = {"tiktok", "instagram", "youtube", "twitter"}

@app.route("/platform/<name>")
def platform(name):
    if name not in PLATFORMS:
        abort(404)
    return render_template(f"{name}.html")

@app.route("/feed")
def feed():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("feed.html", posts=[])

@app.route("/messages")
def messages():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("messages_inbox.html", users=[])

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/use_tool", methods=["POST"])
def use_tool():
    if not login_required():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify({"status": "success", "data": data})

# --------------------
# Errors
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --------------------
# Run (Render compatible)
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
