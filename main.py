from flask import Flask, render_template

app = Flask(__name__)

# --------------------
# ROUTES
# --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/post")
def post():
    return render_template("Post.html")

@app.route("/health")
def health():
    return "OK"

# --------------------
# 404 HANDLER
# --------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
