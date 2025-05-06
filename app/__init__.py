from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.utils.filters import datetime_filter, format_time

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = "very-secure-random-2025"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fastbloom.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.jinja_env.filters["datetime"] = datetime_filter
    app.jinja_env.filters["format_time"] = format_time

    db.init_app(app)

    from app.controllers.main import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app