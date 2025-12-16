from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Index.html")

@app.route("/tiktok")
def tiktok():
    return render_template("Tictok.html")

@app.route("/instagram")
def instagram():
    return render_template("instagram.html")

@app.route("/youtube")
def youtube():
    return render_template("youtube.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
