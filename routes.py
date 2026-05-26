# c:\Users\Lenovo\PycharmProjects\study_buddy\routes.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from app import app
from models import (
    db, User, Task, Pomodoro, Schedule, Emotion, Notification,
    BuddyRelation, BuddyRequest, TaskVisibility, TeamTask, TeamTaskParticipant, Interaction
)
import os
from werkzeug.utils import secure_filename

# 状态常量
# 任务状态: 1=pending(未开始), 2=in_progress(进行中), 3=completed(已完成), 4=overdue(逾期)
# 任务分类: 1=学习, 2=作业, 3=考试, 4=生活
# 任务优先级: 1=重要紧急, 2=重要不紧急, 3=紧急不重要, 4=不重要不紧急
# 可见性: 1=private(仅自己), 2=all_buddies(所有搭子), 3=specific_buddies(指定搭子)
# 情绪类型: 1=happy(开心), 2=calm(平静), 3=anxious(焦虑), 4=tired(疲惫), 5=frustrated(沮丧)
# 通知类型: 1=buddy_request(搭子申请), 2=study_invite(自习邀请), 3=task_reminder(任务提醒), 4=overdue_reminder(逾期提醒)
# 搭子申请状态: 1=pending, 2=accepted, 3=rejected
# 番茄钟状态: 1=completed, 2=interrupted

TASK_STATUS = {1: '未开始', 2: '进行中', 3: '已完成', 4: '逾期'}
TASK_CATEGORY = {1: '学习', 2: '作业', 3: '考试', 4: '生活'}
PRIORITY_TEXT = {1: '重要紧急', 2: '重要不紧急', 3: '紧急不重要', 4: '不重要不紧急'}
EMOTION_TEXT = {1: '开心', 2: '平静', 3: '焦虑', 4: '疲惫', 5: '沮丧'}
NOTIFICATION_TYPE = {1: '搭子申请', 2: '自习邀请', 3: '任务提醒', 4: '逾期提醒'}

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        user = User.query.filter(
            (User.username == identifier) | (User.invite_code == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('用户名/邀请码或密码错误')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))

        invite_code = User.generate_invite_code()
        while User.query.filter_by(invite_code=invite_code).first():
            invite_code = User.generate_invite_code()

        user = User(username=username, invite_code=invite_code)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)
    
    today_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status != 3
    ).filter(
        ((Task.deadline >= today_start) & (Task.deadline < today_end)) |
        (Task.deadline.is_(None)) |
        ((Task.start_time >= today_start) & (Task.start_time < today_end))
    ).order_by(Task.is_top.desc(), Task.deadline).all()

    today_start = datetime(today.year, today.month, today.day)
    today_pomodoros = Pomodoro.query.filter(
        Pomodoro.user_id == current_user.id,
        Pomodoro.start_time >= today_start,
        Pomodoro.status == 1
    ).all()
    today_focus_time = sum(p.duration for p in today_pomodoros)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    total_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.created_at >= week_start,
        Task.created_at < week_end
    ).count()
    completed_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 3,
        Task.updated_at >= week_start,
        Task.updated_at < week_end
    ).count()
    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('dashboard.html',
                         today_tasks=today_tasks,
                         today_focus_time=today_focus_time,
                         completion_rate=completion_rate,
                         unread_count=unread_count,
                         task_status=TASK_STATUS,
                         task_category=TASK_CATEGORY)

@app.route('/profile')
@login_required
def profile():
    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)
    today_pomodoros = Pomodoro.query.filter(
        Pomodoro.user_id == current_user.id,
        Pomodoro.start_time >= today_start,
        Pomodoro.status == 1
    ).all()
    today_focus_time = sum(p.duration for p in today_pomodoros)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    total_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.created_at >= week_start,
        Task.created_at < week_end
    ).count()
    completed_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 3,
        Task.updated_at >= week_start,
        Task.updated_at < week_end
    ).count()
    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('profile.html',
                         today_focus_time=today_focus_time,
                         completion_rate=completion_rate,
                         unread_count=unread_count,
                         emotion_text=EMOTION_TEXT)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.nickname = request.form['nickname']
        current_user.bio = request.form['bio']

        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                current_user.avatar = filename

        db.session.commit()
        flash('个人资料更新成功')
        return redirect(url_for('profile'))

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('edit_profile.html', unread_count=unread_count)

@app.route('/tasks')
@login_required
def tasks():
    filter_status = request.args.get('status', 'all')
    filter_category = request.args.get('category', 'all')

    query = Task.query.filter_by(user_id=current_user.id)

    if filter_status != 'all':
        if filter_status == 'pending':
            query = query.filter_by(status=1)
        elif filter_status == 'in_progress':
            query = query.filter_by(status=2)
        elif filter_status == 'completed':
            query = query.filter_by(status=3)
        elif filter_status == 'overdue':
            query = query.filter_by(status=4)

    if filter_category != 'all':
        category_map = {'学习': 1, '作业': 2, '考试': 3, '生活': 4}
        query = query.filter_by(category=category_map.get(filter_category, 1))

    tasks = query.order_by(Task.is_top.desc(), Task.deadline).all()

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('tasks.html', tasks=tasks,
                         filter_status=filter_status,
                         filter_category=filter_category,
                         unread_count=unread_count,
                         task_status=TASK_STATUS,
                         task_category=TASK_CATEGORY)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        category_map = {'学习': 1, '作业': 2, '考试': 3, '生活': 4}
        visibility_map = {'private': 1, 'all_buddies': 2, 'specific_buddies': 3}

        task = Task(
            user_id=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            category=category_map.get(request.form['category'], 1),
            priority=int(request.form['priority']),
            status=1,
            visibility=visibility_map.get(request.form['visibility'], 1)
        )

        if request.form['start_time']:
            task.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        if request.form['deadline']:
            task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')

        db.session.add(task)
        db.session.commit()

        if task.visibility == 3 and request.form.getlist('visible_buddies'):
            for buddy_id in request.form.getlist('visible_buddies'):
                visibility = TaskVisibility(task_id=task.id, buddy_id=int(buddy_id))
                db.session.add(visibility)
            db.session.commit()

        flash('任务添加成功')
        return redirect(url_for('tasks'))

    buddies = current_user.get_buddies()
    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('add_task.html', buddies=buddies, unread_count=unread_count,
                         task_category=TASK_CATEGORY, priority_text=PRIORITY_TEXT)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('无权访问此任务')
        return redirect(url_for('tasks'))

    if request.method == 'POST':
        category_map = {'学习': 1, '作业': 2, '考试': 3, '生活': 4}
        visibility_map = {'private': 1, 'all_buddies': 2, 'specific_buddies': 3}

        task.title = request.form['title']
        task.description = request.form['description']
        task.category = category_map.get(request.form['category'], 1)
        task.priority = int(request.form['priority'])
        task.visibility = visibility_map.get(request.form['visibility'], 1)
        task.updated_at = datetime.utcnow()

        if request.form['start_time']:
            task.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        if request.form['deadline']:
            task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')

        if task.visibility == 3:
            TaskVisibility.query.filter_by(task_id=task.id).delete()
            for buddy_id in request.form.getlist('visible_buddies'):
                visibility = TaskVisibility(task_id=task.id, buddy_id=int(buddy_id))
                db.session.add(visibility)

        db.session.commit()
        flash('任务更新成功')
        return redirect(url_for('tasks'))

    buddies = current_user.get_buddies()
    visible_buddy_ids = [vb.buddy_id for vb in task.visible_buddies]
    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('edit_task.html', task=task, buddies=buddies,
                         visible_buddy_ids=visible_buddy_ids,
                         unread_count=unread_count,
                         task_category=TASK_CATEGORY,
                         priority_text=PRIORITY_TEXT)

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('无权删除此任务')
        return redirect(url_for('tasks'))

    db.session.delete(task)
    db.session.commit()
    flash('任务删除成功')
    return redirect(url_for('tasks'))

@app.route('/top_task/<int:task_id>')
@login_required
def top_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('无权操作此任务')
        return redirect(url_for('tasks'))

    task.is_top = not task.is_top
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/update_task_status/<int:task_id>/<int:status>')
@login_required
def update_task_status(task_id, status):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'})

    task.status = status
    if status == 3:
        task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})

@app.route('/tasks_quadrant')
@login_required
def tasks_quadrant():
    tasks = Task.query.filter_by(user_id=current_user.id, status=1).all()

    quadrant1 = [t for t in tasks if t.priority == 1]
    quadrant2 = [t for t in tasks if t.priority == 2]
    quadrant3 = [t for t in tasks if t.priority == 3]
    quadrant4 = [t for t in tasks if t.priority == 4]

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('tasks_quadrant.html',
                         quadrant1=quadrant1, quadrant2=quadrant2,
                         quadrant3=quadrant3, quadrant4=quadrant4,
                         unread_count=unread_count,
                         task_status=TASK_STATUS,
                         task_category=TASK_CATEGORY,
                         priority_text=PRIORITY_TEXT)

@app.route('/update_task_priority', methods=['POST'])
@login_required
def update_task_priority():
    data = request.get_json()
    task_id = data['task_id']
    new_priority = data['priority']

    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'})

    task.priority = new_priority
    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})

@app.route('/pomodoro')
@login_required
def pomodoro():
    tasks = Task.query.filter_by(user_id=current_user.id, status=1).all()

    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)
    today_count = Pomodoro.query.filter(
        Pomodoro.user_id == current_user.id,
        Pomodoro.start_time >= today_start,
        Pomodoro.status == 1
    ).count()

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('pomodoro.html', tasks=tasks, today_count=today_count, unread_count=unread_count)

@app.route('/save_pomodoro', methods=['POST'])
@login_required
def save_pomodoro():
    data = request.get_json()

    pomodoro = Pomodoro(
        user_id=current_user.id,
        task_id=data.get('task_id'),
        duration=data['duration'],
        start_time=datetime.fromtimestamp(data['start_time'] / 1000),
        end_time=datetime.fromtimestamp(data['end_time'] / 1000),
        status=data['status'],
        interrupt_reason=data.get('interrupt_reason')
    )

    db.session.add(pomodoro)
    db.session.commit()

    return jsonify({'success': True, 'id': pomodoro.id})

@app.route('/buddies')
@login_required
def buddies():
    buddies = current_user.get_buddies()

    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)

    buddy_stats = []
    for buddy in buddies:
        pomodoros = Pomodoro.query.filter(
            Pomodoro.user_id == buddy.id,
            Pomodoro.start_time >= today_start,
            Pomodoro.status == 1
        ).all()
        focus_time = sum(p.duration for p in pomodoros)
        buddy_stats.append({
            'user': buddy,
            'today_focus': focus_time
        })

    buddy_stats.sort(key=lambda x: x['today_focus'], reverse=True)

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('buddies.html', buddy_stats=buddy_stats, unread_count=unread_count)

@app.route('/buddy/<int:buddy_id>')
@login_required
def buddy_detail(buddy_id):
    buddy = User.query.get_or_404(buddy_id)

    if not current_user.is_buddy_with(buddy_id):
        flash('不是你的搭子，无法查看')
        return redirect(url_for('buddies'))

    tasks = Task.query.filter_by(user_id=buddy_id).filter(
        (Task.visibility == 2) | (Task.visibility == 3)
    ).all()

    visible_tasks = []
    for task in tasks:
        if task.visibility == 2:
            visible_tasks.append(task)
        elif task.visibility == 3:
            visible_buddy_ids = [vb.buddy_id for vb in task.visible_buddies]
            if current_user.id in visible_buddy_ids:
                visible_tasks.append(task)

    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)
    today_pomodoros = Pomodoro.query.filter(
        Pomodoro.user_id == buddy_id,
        Pomodoro.start_time >= today_start,
        Pomodoro.status == 1
    ).all()
    today_focus = sum(p.duration for p in today_pomodoros)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    week_pomodoros = Pomodoro.query.filter(
        Pomodoro.user_id == buddy_id,
        Pomodoro.start_time >= week_start,
        Pomodoro.start_time < week_end,
        Pomodoro.status == 1
    ).all()
    week_focus = sum(p.duration for p in week_pomodoros)

    schedules = Schedule.query.filter_by(user_id=buddy_id, visibility=2).all()
    emotions = Emotion.query.filter_by(user_id=buddy_id, visibility=2).order_by(Emotion.created_at.desc()).limit(7).all()

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('buddy_detail.html',
                         buddy=buddy,
                         tasks=visible_tasks,
                         today_focus=today_focus,
                         week_focus=week_focus,
                         schedules=schedules,
                         emotions=emotions,
                         unread_count=unread_count,
                         task_status=TASK_STATUS,
                         task_category=TASK_CATEGORY,
                         emotion_text=EMOTION_TEXT)

@app.route('/add_buddy', methods=['GET', 'POST'])
@login_required
def add_buddy():
    if request.method == 'POST':
        invite_code = request.form['invite_code'].strip().upper()

        if invite_code == current_user.invite_code:
            flash('不能添加自己为搭子')
            return redirect(url_for('add_buddy'))

        user = User.query.filter_by(invite_code=invite_code).first()
        if not user:
            flash('邀请码无效')
            return redirect(url_for('add_buddy'))

        if current_user.is_buddy_with(user.id):
            flash('已经是搭子关系')
            return redirect(url_for('add_buddy'))

        existing_request = BuddyRequest.query.filter(
            (BuddyRequest.requester_id == current_user.id) &
            (BuddyRequest.target_id == user.id) &
            (BuddyRequest.status == 1)
        ).first()

        if existing_request:
            flash('申请已发送，请等待对方确认')
            return redirect(url_for('add_buddy'))

        request_entry = BuddyRequest(
            requester_id=current_user.id,
            target_id=user.id,
            status=1
        )
        db.session.add(request_entry)

        notification = Notification(
            user_id=user.id,
            type=1,
            content=f'{current_user.nickname} 申请成为你的学习搭子',
            related_id=request_entry.id
        )
        db.session.add(notification)

        db.session.commit()
        flash('申请已发送，请等待对方确认')
        return redirect(url_for('buddies'))

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('add_buddy.html', unread_count=unread_count)

@app.route('/handle_buddy_request/<int:request_id>/<string:action>')
@login_required
def handle_buddy_request(request_id, action):
    buddy_request = BuddyRequest.query.get_or_404(request_id)

    if buddy_request.target_id != current_user.id:
        flash('无权处理此申请')
        return redirect(url_for('notifications'))

    if action == 'accept':
        relation1 = BuddyRelation(user_id=current_user.id, buddy_id=buddy_request.requester_id)
        relation2 = BuddyRelation(user_id=buddy_request.requester_id, buddy_id=current_user.id)
        db.session.add(relation1)
        db.session.add(relation2)

        buddy_request.status = 2

        notification = Notification(
            user_id=buddy_request.requester_id,
            type=1,
            content=f'{current_user.nickname} 同意了你的搭子申请'
        )
        db.session.add(notification)

        flash('已同意搭子申请')
    elif action == 'reject':
        buddy_request.status = 3
        flash('已拒绝搭子申请')

    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/remove_buddy/<int:buddy_id>')
@login_required
def remove_buddy(buddy_id):
    BuddyRelation.query.filter(
        ((BuddyRelation.user_id == current_user.id) & (BuddyRelation.buddy_id == buddy_id)) |
        ((BuddyRelation.user_id == buddy_id) & (BuddyRelation.buddy_id == current_user.id))
    ).delete()

    db.session.commit()
    flash('已解除搭子关系')
    return redirect(url_for('buddies'))

@app.route('/schedule')
@login_required
def schedule():
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(
        Schedule.day_of_week, Schedule.start_period
    ).all()

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('schedule.html',
                         schedules=schedules,
                         week_days=week_days,
                         unread_count=unread_count)

@app.route('/import_schedule')
@login_required
def import_schedule():
    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('import_schedule.html', unread_count=unread_count)

@app.route('/add_schedule', methods=['GET', 'POST'])
@login_required
def add_schedule():
    quick_courses = [
        {'name': '高等数学', 'teacher': ''},
        {'name': '线性代数', 'teacher': ''},
        {'name': '大学英语', 'teacher': ''},
        {'name': '计算机基础', 'teacher': ''},
        {'name': '程序设计', 'teacher': ''},
        {'name': '数据结构', 'teacher': ''},
        {'name': '操作系统', 'teacher': ''},
        {'name': '数据库原理', 'teacher': ''},
    ]
    
    if request.method == 'POST':
        schedule = Schedule(
            user_id=current_user.id,
            course_name=request.form['course_name'],
            teacher=request.form.get('teacher', ''),
            location=request.form.get('location', ''),
            day_of_week=int(request.form['day_of_week']),
            start_period=int(request.form['start_period']),
            end_period=int(request.form['end_period']),
            week_range=request.form.get('week_range', ''),
            visibility=1
        )
        db.session.add(schedule)
        db.session.commit()
        flash('课程添加成功')
        return redirect(url_for('schedule'))
    
    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return render_template('add_schedule.html', 
                         unread_count=unread_count,
                         quick_courses=quick_courses)

@app.route('/save_schedule', methods=['POST'])
@login_required
def save_schedule():
    data = request.get_json()
    courses = data.get('courses', [])

    for course in courses:
        schedule = Schedule(
            user_id=current_user.id,
            course_name=course['course_name'],
            teacher=course.get('teacher', ''),
            location=course.get('location', ''),
            day_of_week=int(course['day_of_week']),
            start_period=int(course['start_period']),
            end_period=int(course['end_period']),
            visibility=1
        )
        db.session.add(schedule)

    db.session.commit()
    return jsonify({'success': True})

@app.route('/update_schedule_visibility', methods=['POST'])
@login_required
def update_schedule_visibility():
    data = request.get_json()
    visibility = 2 if data['visibility'] == 'all_buddies' else 1

    Schedule.query.filter_by(user_id=current_user.id).update({'visibility': visibility})
    db.session.commit()

    return jsonify({'success': True})

@app.route('/match_schedule')
@login_required
def match_schedule():
    buddies = current_user.get_buddies()
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_buddy_id = request.args.get('buddy_id', type=int)

    match_result = []

    if selected_buddy_id:
        buddy = User.query.get(selected_buddy_id)
        if buddy:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
            day_of_week = date_obj.isoweekday()

            my_schedules = Schedule.query.filter(
                Schedule.user_id == current_user.id,
                Schedule.day_of_week == day_of_week
            ).all()

            buddy_schedules = Schedule.query.filter(
                Schedule.user_id == buddy.id,
                Schedule.day_of_week == day_of_week,
                Schedule.visibility == 2
            ).all()

            all_periods = set(range(1, 13))

            my_busy_periods = set()
            for s in my_schedules:
                my_busy_periods.update(range(s.start_period, s.end_period + 1))

            buddy_busy_periods = set()
            for s in buddy_schedules:
                buddy_busy_periods.update(range(s.start_period, s.end_period + 1))

            free_periods = all_periods - my_busy_periods - buddy_busy_periods

            if free_periods:
                sorted_periods = sorted(free_periods)
                start = sorted_periods[0]
                end = start

                for p in sorted_periods[1:]:
                    if p == end + 1:
                        end = p
                    else:
                        match_result.append({'start': start, 'end': end})
                        start = p
                        end = p
                match_result.append({'start': start, 'end': end})

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('match_schedule.html',
                         buddies=buddies,
                         selected_date=selected_date,
                         selected_buddy_id=selected_buddy_id,
                         match_result=match_result,
                         unread_count=unread_count)

@app.route('/send_study_invite', methods=['POST'])
@login_required
def send_study_invite():
    data = request.get_json()
    buddy_id = data['buddy_id']
    date = data['date']
    start_period = data['start_period']
    end_period = data['end_period']

    buddy = User.query.get(buddy_id)
    if not buddy:
        return jsonify({'success': False, 'message': '搭子不存在'})

    notification = Notification(
        user_id=buddy_id,
        type=2,
        content=f'{current_user.nickname} 邀请你于 {date} 第{start_period}-{end_period}节课一起自习',
        related_id=current_user.id
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': '邀请已发送'})

@app.route('/emotion')
@login_required
def emotion():
    emotions = Emotion.query.filter_by(user_id=current_user.id).order_by(Emotion.created_at.desc()).all()

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('emotion.html', emotions=emotions, unread_count=unread_count,
                         emotion_text=EMOTION_TEXT)

@app.route('/add_emotion', methods=['POST'])
@login_required
def add_emotion():
    emotion_type_map = {'happy': 1, 'calm': 2, 'anxious': 3, 'tired': 4, 'frustrated': 5}
    visibility_map = {'private': 1, 'all_buddies': 2}

    emotion_type = request.form['emotion_type']
    note = request.form.get('note', '')
    visibility = visibility_map.get(request.form.get('visibility', 'private'), 1)

    emotion = Emotion(
        user_id=current_user.id,
        emotion_type=emotion_type_map.get(emotion_type, 1),
        note=note[:100] if note else '',
        visibility=visibility
    )

    db.session.add(emotion)
    db.session.commit()

    flash('情绪记录成功')
    return redirect(url_for('emotion'))

@app.route('/delete_emotion/<int:emotion_id>')
@login_required
def delete_emotion(emotion_id):
    emotion = Emotion.query.get_or_404(emotion_id)
    if emotion.user_id != current_user.id:
        flash('无权删除')
        return redirect(url_for('emotion'))

    db.session.delete(emotion)
    db.session.commit()
    flash('已删除')
    return redirect(url_for('emotion'))

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('notifications.html', notifications=notifications,
                         notification_type=NOTIFICATION_TYPE)

@app.route('/stats')
@login_required
def stats():
    today = datetime.now().date()

    task_stats = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)

        total = Task.query.filter(
            Task.user_id == current_user.id,
            Task.created_at < end
        ).count()

        completed = Task.query.filter(
            Task.user_id == current_user.id,
            Task.status == 3,
            Task.updated_at >= start,
            Task.updated_at < end
        ).count()

        rate = round((completed / total) * 100) if total > 0 else 0
        task_stats.append({'date': date.strftime('%m-%d'), 'rate': rate})

    focus_stats = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)

        pomodoros = Pomodoro.query.filter(
            Pomodoro.user_id == current_user.id,
            Pomodoro.start_time >= start,
            Pomodoro.start_time < end,
            Pomodoro.status == 1
        ).all()

        duration = sum(p.duration for p in pomodoros)
        focus_stats.append({'date': date.strftime('%m-%d'), 'duration': duration})

    category_stats = []
    categories = [1, 2, 3, 4]
    category_names = ['学习', '作业', '考试', '生活']
    for category in categories:
        pomodoros = Pomodoro.query.join(Task).filter(
            Pomodoro.user_id == current_user.id,
            Task.category == category,
            Pomodoro.status == 1
        ).all()
        duration = sum(p.duration for p in pomodoros)
        category_stats.append({'name': category_names[category-1], 'value': duration})

    heatmap_data = []
    for hour in range(0, 24):
        for day in range(7):
            date = today - timedelta(days=6 - day)
            start = datetime(date.year, date.month, date.day, hour, 0, 0)
            end = start + timedelta(hours=1)

            pomodoros = Pomodoro.query.filter(
                Pomodoro.user_id == current_user.id,
                Pomodoro.start_time >= start,
                Pomodoro.start_time < end,
                Pomodoro.status == 1
            ).all()

            count = len(pomodoros)
            if count > 0:
                heatmap_data.append([day, hour, count])

    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('stats.html',
                         task_stats=task_stats,
                         focus_stats=focus_stats,
                         category_stats=category_stats,
                         heatmap_data=heatmap_data,
                         unread_count=unread_count)

@app.route('/like_task/<int:task_id>')
@login_required
def like_task(task_id):
    task = Task.query.get_or_404(task_id)

    existing_like = Interaction.query.filter(
        Interaction.from_user_id == current_user.id,
        Interaction.task_id == task_id,
        Interaction.type == 1
    ).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'success': True, 'liked': False})
    else:
        like = Interaction(
            from_user_id=current_user.id,
            to_user_id=task.user_id,
            task_id=task_id,
            type=1
        )
        db.session.add(like)
        db.session.commit()
        return jsonify({'success': True, 'liked': True})

@app.route('/comment_task', methods=['POST'])
@login_required
def comment_task():
    data = request.get_json()
    task_id = data['task_id']
    content = data['content'][:20] if data['content'] else ''

    task = Task.query.get_or_404(task_id)

    comment = Interaction(
        from_user_id=current_user.id,
        to_user_id=task.user_id,
        task_id=task_id,
        type=2,
        content=content
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/create_team_task', methods=['GET', 'POST'])
@login_required
def create_team_task():
    if request.method == 'POST':
        task = TeamTask(
            title=request.form['title'],
            description=request.form['description']
        )

        if request.form['deadline']:
            task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')

        db.session.add(task)
        db.session.commit()

        creator = TeamTaskParticipant(
            team_task_id=task.id,
            user_id=current_user.id,
            role=1
        )
        db.session.add(creator)

        for buddy_id in request.form.getlist('buddies'):
            participant = TeamTaskParticipant(
                team_task_id=task.id,
                user_id=int(buddy_id),
                role=2
            )
            db.session.add(participant)

            notification = Notification(
                user_id=int(buddy_id),
                type=3,
                content=f'{current_user.nickname} 邀请你参与组队任务：{task.title}',
                related_id=task.id
            )
            db.session.add(notification)

        db.session.commit()
        flash('组队任务创建成功')
        return redirect(url_for('dashboard'))

    buddies = current_user.get_buddies()
    unread_count = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template('create_team_task.html', buddies=buddies, unread_count=unread_count)

@app.route('/update_team_task_status/<int:task_id>/<int:status>')
@login_required
def update_team_task_status(task_id, status):
    task = TeamTask.query.get_or_404(task_id)

    participant = TeamTaskParticipant.query.filter(
        TeamTaskParticipant.team_task_id == task_id,
        TeamTaskParticipant.user_id == current_user.id
    ).first()

    if not participant:
        flash('无权操作此任务')
        return redirect(url_for('dashboard'))

    task.status = status
    task.updated_at = datetime.utcnow()
    db.session.commit()

    flash('任务状态已更新')
    return redirect(url_for('dashboard'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']