import os
from flask import Flask
from config import config_by_name
from app.database.connection import close_db, init_db

def create_app(config_name='development'):
    app_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__,
                static_folder=os.path.join(app_dir, 'static'),
                template_folder=os.path.join(app_dir, 'templates'))
                
    app.config.from_object(config_by_name[config_name])

    # Database setup & teardown
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)

    return app
