from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db, init_db

# --------------------
# Flask app setup
# --------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Initialize database
init_db()

# --------------------
# ROUTES
# --------------------

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")

# Dashboard page
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# --------------------
# Run locally
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
