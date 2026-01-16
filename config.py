import os
from datetime import timedelta

# Get the base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Production-grade Flask configuration"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # ============================================================
    # DATABASE CONFIGURATION (UPDATED FOR RENDER)
    # ============================================================
    # Render humein 'postgres://' deta hai, par SQLAlchemy ko 'postgresql://' chahiye hota hai.
    # Hum yahan check kar rahe hain aur fix kar rahe hain.
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    # Agar cloud URL mila toh wo use karega, nahi toh local sqlite use karega
    SQLALCHEMY_DATABASE_URI = database_url or f'sqlite:///{os.path.join(BASE_DIR, "nutritrack.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL debugging
    
    # ============================================================
    # SESSION & APP SETTINGS
    # ============================================================
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    JSON_SORT_KEYS = False
    
    # Data Path
NUTRITION_CSV_PATH = os.path.join(BASE_DIR, 'nutrition_data.csv')
