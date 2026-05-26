# c:\Users\Lenovo\PycharmProjects\study_buddy\config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask 密钥（用于会话加密）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-strong-secret-key-change-this-in-production'
    
    # 数据库连接配置
    # 本地开发: mysql+pymysql://root:@localhost/study_buddy
    # PythonAnywhere: mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/username$study_buddy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/study_buddy'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 生产环境配置
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'