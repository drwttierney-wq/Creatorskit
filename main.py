from flask import Flask, render_template, request, redirect, session
import sqlite3
from ai_engine import viral_hooks, captions, hashtags, content_plan

app = Flask(__name__)
app.secret_key = "supersecretkey"
DB = "database.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ideas (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        platform TEXT,
        content TEXT,
        public INTEGER DEFAULT 0
    )""")

    c.commit()
    c.close()

init()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        db().execute("INSERT INTO users VALUES (NULL,?,?)",
        (request.form["username"], request.form["password"]))
        db().commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        user = db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()
        if user:
            session["id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "id" not in session: return redirect("/login")
    return render_template("dashboard.html")

@app.route("/platform/<name>", methods=["GET","POST"])
def platform(name):
    if "id" not in session: return redirect("/login")

    ai_result = None

    if request.method == "POST":
        niche = request.form["niche"]
        tool = request.form["tool"]

        if tool == "hooks":
            ai_result = viral_hooks(niche)
        elif tool == "captions":
            ai_result = captions(niche)
        elif tool == "hashtags":
            ai_result = hashtags(niche)
        elif tool == "plan":
            ai_result = content_plan(niche)

    return render_template("platform.html", platform=name, result=ai_result)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
