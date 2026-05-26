# c:\Users\Lenovo\PycharmProjects\study_buddy\config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask 密钥（用于会话加密）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-strong-secret-key-change-this-in-production'
    
    # 数据库连接配置
    # Render PostgreSQL: postgresql://username:password@host:port/database
    # 本地开发（SQLite）: sqlite:///app.db
    # MySQL: mysql+pymysql://username:password@host/database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # 根据环境选择数据库
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace('postgres://', 'postgresql://')
    elif DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 默认使用 SQLite（开发环境）
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 生产环境配置
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'