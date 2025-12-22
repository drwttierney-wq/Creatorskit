from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "creatorskit-secret"


# --------------------
# BASIC PAGES
# --------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# --------------------
# PLATFORM PAGES
# --------------------

@app.route("/platform/<name>")
def platform(name):
    return render_template(f"{name}.html")


# --------------------
# COMMUNITY
# --------------------

@app.route("/feed")
def feed():
    return render_template("feed.html", posts=[])


@app.route("/post")
def post():
    return render_template("post.html", saved=[])


@app.route("/messages")
def messages():
    return render_template("messages_inbox.html", users=[])


# --------------------
# FALLBACK (optional)
# --------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404


# --------------------
# LOCAL RUN
# --------------------

if __name__ == "__main__":
    app.run(debug=True)
