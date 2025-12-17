import os
from flask import Flask, render_template, request, redirect, session
from database import init_db

app = Flask(__name__)
app.secret_key = "super-secret-key"  # change later

# Initialize database
init_db()

# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def index():
    return render_template("Index.html")

@app.route("/platform")
def platform():
    return render_template("platform.html")

@app.route("/tiktok")
def tiktok():
    return render_template("Tictok.html")

@app.route("/instagram")
def instagram():
    return render_template("instagram.html")

@app.route("/youtube")
def youtube():
    return render_template("youtube.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

# -----------------------
# RUN
# -----------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
