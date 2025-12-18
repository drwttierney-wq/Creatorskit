from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return "CreatorsKit is running 🚀"

@app.route("/youtube")
def youtube():
    return render_template("youtube.html")

if __name__ == "__main__":
    app.run()
