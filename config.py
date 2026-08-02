import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shridevi-fallback-secret-key'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://mongodb:27017/marks_analyser'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/marks_analyser'

class ProductionConfig(Config):
    DEBUG = False
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://mongodb:27017/marks_analyser'

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/marks_analyser_test'

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
