import os
from dotenv import load_dotenv

# Determine the base directory of the backend application
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Load environment variables from .env file located in the Backend directory
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default SQLite database URI if not set in .env
    # The 'instance_relative_config=True' in app factory will place it in 'instance' folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'community_pulse.db')

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:3000' # Adjust if your Vue port is different

    # APScheduler
    SCHEDULER_API_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False # Set to True to see SQL queries

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for testing forms if you use Flask-WTF

class ProductionConfig(Config):
    DEBUG = False
    # Add other production-specific settings here

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}