from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user

app = Flask(__name__)
app.secret_key = "super-secret-key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---- TEMP USER MODEL (STABLE) ----
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {"admin": {"password": "admin"}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ---- AUTH ----
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            login_user(User(username))
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---- CORE PAGES ----
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ---- PLATFORM ROUTES (MATCH FILE NAMES EXACTLY) ----
platforms = [
    "Facebook","instagram","twitter","tictok","snapchat","youtube",
    "linkedin","pinterest","threads","discord","reddit","twitch"
]

for p in platforms:
    def page(p=p):
        return render_template(f"{p}.html")
    app.add_url_rule(f"/{p}", p, login_required(page))

# ---- TOOL ENDPOINT ----
@app.route("/use_tool", methods=["POST"])
@login_required
def use_tool():
    data = request.json
    return jsonify({
        "status": "success",
        "platform": data["platform"],
        "tool": data["tool"]
    })

if __name__ == "__main__":
    app.run()
