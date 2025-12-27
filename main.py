from flask import Flask, render_template

app = Flask(__name__)

# --------------------
# CORE PAGES
# --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/post")
def post():
    return render_template("Post.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

# --------------------
# AUTH
# --------------------

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

# --------------------
# HEALTH CHECK (IMPORTANT)
# --------------------

@app.route("/health")
def health():
    return "OK"

# --------------------
# 404 PAGE
# --------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
