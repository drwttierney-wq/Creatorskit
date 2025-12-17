import os
import sqlite3
from flask import Flask, render_template, request, redirect, session
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = "supersecretkey"

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            return redirect("/login")
        except:
            return "Username already exists"

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect("/platform")
        else:
            return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/platform")
def platform():
    if "user" not in session:
        return redirect("/login")
    return render_template("platform.html")

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    return render_template("profile.html")

@app.route("/tiktok")
def tiktok():
    return render_template("tiktok.html")

@app.route("/instagram")
def instagram():
    return render_template("instagram.html")

@app.route("/youtube")
def youtube():
    return render_template("youtube.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
