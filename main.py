from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "database.db"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        platform TEXT,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                         (username,password))
            conn.commit()
        except:
            return "Username already exists"
        conn.close()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/platform/<name>", methods=["GET","POST"])
def platform(name):
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        content = request.form["content"]
        conn = get_db()
        conn.execute(
            "INSERT INTO ideas (user_id, platform, content) VALUES (?,?,?)",
            (session["user_id"], name, content)
        )
        conn.commit()
        conn.close()

    conn = get_db()
    ideas = conn.execute(
        "SELECT * FROM ideas WHERE user_id=? AND platform=?",
        (session["user_id"], name)
    ).fetchall()
    conn.close()

    return render_template("platform.html", platform=name, ideas=ideas)

if __name__ == "__main__":
    app.run()
