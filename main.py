from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from database import db, Post  # your existing database logic if you had it

app = Flask(__name__)
app.secret_key = "creators-kit-secret"

# --------------------
# CORE ROUTES
# --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/community")
def community():
    # This fixes your previous 404 issue
    # You can later add dynamic posts using your database
    return render_template("community.html")

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "POST":
        # Example: saving post to database
        title = request.form.get("title")
        content = request.form.get("content")
        if title and content:
            new_post = Post(title=title, content=content)
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("community"))
    return render_template("Post.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

# --------------------
# AUTH ROUTES
# --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("username", "user")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["user"] = request.form.get("username", "user")
        return redirect(url_for("dashboard"))
    return render_template("register.html")

# --------------------
# HEALTH CHECK
# --------------------

@app.route("/health")
def health():
    return "OK"

# --------------------
# 404 ERROR PAGE
# --------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --------------------
# ONLY LOCAL DEBUG (Render ignores this)
# --------------------

if __name__ == "__main__":
    app.run(debug=True)
