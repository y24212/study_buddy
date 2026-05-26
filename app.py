# c:\Users\Lenovo\PycharmProjects\study_buddy\app.py
from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 启用 CSRF 保护
csrf = CSRFProtect()
csrf.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 导入路由
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)