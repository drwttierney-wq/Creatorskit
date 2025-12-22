from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "creators-kit-secret"

# --------------------
# AUTH (SIMPLE & STABLE)
# --------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("username", "user")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def require_login():
    return "user" in session


# --------------------
# CORE PAGE
# --------------------
@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("dashboard.html")


# --------------------
# PLATFORM ROUTES
# --------------------
PLATFORMS = [
    "Facebook",
    "instagram",
    "twitter",
    "tictok",
    "snapchat",
    "youtube",
    "linkedin",
    "pinterest",
    "threads",
    "discord",
    "reddit",
    "twitch"
]

for platform in PLATFORMS:
    def make_view(name):
        def view():
            if not require_login():
                return redirect(url_for("login"))
            return render_template(f"{name}.html")
        return view

    app.add_url_rule(
        f"/{platform}",
        platform,
        make_view(platform)
    )


# --------------------
# TOOL ENDPOINT
# --------------------
@app.route("/use_tool", methods=["POST"])
def use_tool():
    if not require_login():
        return jsonify({"status": "unauthorized"}), 401

    data = request.get_json(force=True)
    return jsonify({
        "status": "success",
        "platform": data.get("platform"),
        "tool": data.get("tool"),
        "content": data.get("content", "")
    })


# --------------------
# ENTRYPOINT
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
