import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from database import db

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# --------------------
# Database setup
# --------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Create DB tables if they don't exist
with app.app_context():
    db.create_all()

# --------------------
# UPLOADS folder
# --------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --------------------
# ROUTES
# --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        session["user"] = username  # TEMP login
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        session["user"] = username  # TEMP register
        return redirect(url_for("dashboard"))
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

@app.route("/messages")
def messages():
    return render_template("messages_inbox.html", users=[])

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/use_tool", methods=["POST"])
def use_tool():
    data = request.get_json()
    print(data)  # TEMP logging
    return jsonify({"status": "success"})

# --------------------
# 404 page
# --------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
