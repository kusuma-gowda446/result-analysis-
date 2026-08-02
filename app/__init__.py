import os
from flask import Flask, render_template
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

    # Register Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    return app
