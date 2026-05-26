# c:\Users\Lenovo\PycharmProjects\study_buddy\models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

db = SQLAlchemy()

# 状态常量定义
# 任务状态: 1=pending(未开始), 2=in_progress(进行中), 3=completed(已完成), 4=overdue(逾期)
# 任务分类: 1=学习, 2=作业, 3=考试, 4=生活
# 任务优先级: 1=重要紧急, 2=重要不紧急, 3=紧急不重要, 4=不重要不紧急
# 可见性: 1=private(仅自己), 2=all_buddies(所有搭子), 3=specific_buddies(指定搭子)
# 情绪类型: 1=happy(开心), 2=calm(平静), 3=anxious(焦虑), 4=tired(疲惫), 5=frustrated(沮丧)
# 通知类型: 1=buddy_request(搭子申请), 2=study_invite(自习邀请), 3=task_reminder(任务提醒), 4=overdue_reminder(逾期提醒)

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # 改为255适配Werkzeug哈希
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    avatar = db.Column(db.String(200), default='default.jpg')
    nickname = db.Column(db.String(50), default='学习者')
    bio = db.Column(db.String(200), default='专注学习，自律成长')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增
    
    # 关系
    tasks = db.relationship('Task', backref='user', lazy=True)
    pomodoros = db.relationship('Pomodoro', backref='user', lazy=True)
    schedules = db.relationship('Schedule', backref='user', lazy=True)
    emotions = db.relationship('Emotion', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    # 搭子关系
    sent_requests = db.relationship('BuddyRequest', foreign_keys='BuddyRequest.requester_id', backref='requester', lazy=True)
    received_requests = db.relationship('BuddyRequest', foreign_keys='BuddyRequest.target_id', backref='target', lazy=True)
    buddy_relations = db.relationship('BuddyRelation', foreign_keys='BuddyRelation.user_id', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_invite_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def get_buddies(self):
        buddy_ids = [rel.buddy_id for rel in self.buddy_relations]
        return User.query.filter(User.id.in_(buddy_ids)).all()
    
    def is_buddy_with(self, user_id):
        return BuddyRelation.query.filter(
            ((BuddyRelation.user_id == self.id) & (BuddyRelation.buddy_id == user_id)) |
            ((BuddyRelation.user_id == user_id) & (BuddyRelation.buddy_id == self.id))
        ).first() is not None

# 搭子关系模型
class BuddyRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buddy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'buddy_id', name='uk_buddy_relation'),
    )

# 搭子申请模型
class BuddyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.SmallInteger, default=1)  # 1=pending, 2=accepted, 3=rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增
    
    __table_args__ = (
        db.UniqueConstraint('requester_id', 'target_id', name='uk_buddy_request'),
    )

# 任务模型
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.SmallInteger, default=1)  # 1=学习, 2=作业, 3=考试, 4=生活
    priority = db.Column(db.SmallInteger, default=2)  # 1-4对应四象限
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=1)  # 1=pending, 2=in_progress, 3=completed, 4=overdue
    is_top = db.Column(db.Boolean, default=False)
    visibility = db.Column(db.SmallInteger, default=1)  # 1=private, 2=all_buddies, 3=specific_buddies
    completed_at = db.Column(db.DateTime)  # 新增：任务完成时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的番茄钟记录
    pomodoros = db.relationship('Pomodoro', backref='task', lazy=True)
    
    # 指定可见的搭子
    visible_buddies = db.relationship('TaskVisibility', backref='task', lazy=True)

# 任务可见性模型
class TaskVisibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    buddy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'buddy_id', name='uk_task_visibility'),
    )

# 番茄钟模型
class Pomodoro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    duration = db.Column(db.Integer, default=25)  # 分钟
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=1)  # 1=completed, 2=interrupted
    interrupt_reason = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增

# 课表模型
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(50))
    location = db.Column(db.String(100))
    day_of_week = db.Column(db.SmallInteger, nullable=False)  # 1-7对应周一到周日
    start_period = db.Column(db.SmallInteger, nullable=False)  # 第几节课开始
    end_period = db.Column(db.SmallInteger, nullable=False)  # 第几节课结束
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    visibility = db.Column(db.SmallInteger, default=1)  # 1=private, 2=all_buddies
    week_range = db.Column(db.String(50))  # 新增：周次范围，如"1-8,10-16"或"单周"或"双周"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增

# 情绪记录模型
class Emotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emotion_type = db.Column(db.SmallInteger, nullable=False)  # 1=happy, 2=calm, 3=anxious, 4=tired, 5=frustrated
    note = db.Column(db.String(100))
    visibility = db.Column(db.SmallInteger, default=1)  # 1=private, 2=all_buddies
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增

# 通知模型
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.SmallInteger, nullable=False)  # 1=buddy_request, 2=study_invite, 3=task_reminder, 4=overdue_reminder
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer)  # 关联的请求ID、任务ID等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增

# 组队任务模型
class TeamTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.SmallInteger, default=1)  # 1=pending, 2=in_progress, 3=completed, 4=overdue
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联用户
    participants = db.relationship('TeamTaskParticipant', backref='team_task', lazy=True)

# 组队任务参与者
class TeamTaskParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_task_id = db.Column(db.Integer, db.ForeignKey('team_task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.SmallInteger, default=2)  # 1=creator, 2=member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增
    
    __table_args__ = (
        db.UniqueConstraint('team_task_id', 'user_id', name='uk_team_participant'),
    )

# 互动记录模型
class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    pomodoro_id = db.Column(db.Integer, db.ForeignKey('pomodoro.id'))
    type = db.Column(db.SmallInteger, nullable=False)  # 1=like, 2=comment
    content = db.Column(db.String(50))  # 评论内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 新增

# 辅助函数：状态码转中文
def get_task_status_text(status):
    status_map = {1: '未开始', 2: '进行中', 3: '已完成', 4: '逾期'}
    return status_map.get(status, '未知')

def get_task_category_text(category):
    category_map = {1: '学习', 2: '作业', 3: '考试', 4: '生活'}
    return category_map.get(category, '未知')

def get_priority_text(priority):
    priority_map = {1: '重要紧急', 2: '重要不紧急', 3: '紧急不重要', 4: '不重要不紧急'}
    return priority_map.get(priority, '未知')

def get_visibility_text(visibility):
    visibility_map = {1: '仅自己可见', 2: '所有搭子可见', 3: '指定搭子可见'}
    return visibility_map.get(visibility, '未知')

def get_emotion_text(emotion_type):
    emotion_map = {1: '开心', 2: '平静', 3: '焦虑', 4: '疲惫', 5: '沮丧'}
    return emotion_map.get(emotion_type, '未知')

def get_notification_type_text(type_code):
    type_map = {1: '搭子申请', 2: '自习邀请', 3: '任务提醒', 4: '逾期提醒'}
    return type_map.get(type_code, '未知')