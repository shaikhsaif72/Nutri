import os
from datetime import timedelta

# Get the base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Production-grade Flask configuration"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "nutritrack.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL debugging
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    JSON_SORT_KEYS = False
    
    # --- FIX YAHAN HAI: NAYI DETAILED FILE KA PATH ---
    # Hum 'Data' folder ke andar 'nutrition_data.csv' use kar rahe hain
    NUTRITION_CSV_PATH = os.path.join(BASE_DIR, 'Data', 'nutrition_data.csv')