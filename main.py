from flask import Flask, render_template
from database import db

app = Flask(__name__)
app.secret_key = "creators-kit-secret"

# DATABASE CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

# REQUIRED FOR GUNICORN
application = app
