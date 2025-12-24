# Database setup for Render (persistent storage)
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join('/data' if os.path.exists('/data') else BASE_DIR, 'instance', 'database.db')
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
