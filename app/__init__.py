from flask import Flask, redirect, jsonify, render_template, request
from app.models import db, User, Bins
from app.routes.routes import routes_bp
from app.routes.auth import auth_bp
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    
    with app.app_context():

        app.register_blueprint(routes_bp)
        app.register_blueprint(auth_bp)

        db.create_all()


    return app