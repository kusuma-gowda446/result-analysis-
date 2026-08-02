import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shridevi-fallback-secret-key'
    DATABASE_PATH = os.path.join(basedir, os.environ.get('DATABASE_PATH') or 'instance/database.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = os.path.join(basedir, 'instance/test_database.db')

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
