from flask import Flask, render_template, session, request, redirect, url_for, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from sqlalchemy import extract

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:20040707sqy@localhost:3306/dxp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sqy'  # 确保这个密钥设置了

# 初始化数据库
db = SQLAlchemy(app)


# 用户表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 密码明文存储
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Enum('管理员', '会员', '游客', name='user_roles'), nullable=False, default='游客')
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))


# 事件表
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # 事件名称
    time = db.Column(db.DateTime, nullable=False)  # 事件发生时间
    process = db.Column(db.Text, nullable=False)  # 事件过程
    effect = db.Column(db.Text, nullable=True)  # 事件作用
    image_link = db.Column(db.String(300), nullable=True)  # 图片链接
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))


# 人物表
class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 人物名字
    gender = db.Column(db.String(10), nullable=False)  # 性别
    birth_date = db.Column(db.Date, nullable=False)  # 出生日期
    death_date = db.Column(db.Date, nullable=True)  # 死亡日期，可为空
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))


# 事件-人物关联表
class EventPerson(db.Model):
    __tablename__ = 'event_person'
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), primary_key=True)  # 事件ID
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id', ondelete='CASCADE'), primary_key=True)  # 人物ID

    # 外键关联
    event = db.relationship('Event', backref=db.backref('event_persons', passive_deletes=True))
    person = db.relationship('Person', backref=db.backref('person_events', passive_deletes=True))


# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']

        # 检查用户名、邮箱或电话是否已存在
        user = User.query.filter((User.username == username) | (User.phone == phone) | (User.email == email)).first()
        if user:
            flash('用户名、邮箱或电话已存在！', 'danger')
            return redirect(url_for('index'))

        # 创建新用户并保存到数据库（明文存储密码）
        new_user = User(username=username, password=password, email=email, phone=phone, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录！', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', form_type='register')


# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 查找用户
        user = User.query.filter_by(username=username, password=password).first()  # 明文密码验证
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['email'] = user.email
            session['phone'] = user.phone
            session['created_at'] = user.created_at
            flash('登录成功！', 'success')
            return redirect(url_for('welcome'))  # 登录成功后跳转到登录后的页面
        else:
            flash('用户名或密码错误！', 'danger')

    return render_template('index.html', form_type='login')


# 找回密码
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']

        # 查找用户
        user = User.query.filter_by(username=username, email=email, phone=phone).first()
        if user:
            flash('验证通过，请检查您的邮箱进行密码重置！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户信息不匹配！', 'danger')

    return render_template('index.html', form_type='reset_password')

@app.route('/welcome')
def welcome():
    if 'user_id' in session:
        return render_template('welcome.html')  # 确保渲染的是 welcome.html
    else:
        flash('请先登录！', 'danger')
        return redirect(url_for('login'))  # 如果没有登录，重定向到登录页面


# 登录后的页面
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('email', None)
    session.pop('phone', None)
    session.pop('created_at', None)
    flash('您已成功退出登录！', 'success')
    return redirect(url_for('login'))  # 退出后重定向到登录页面


# 事件查询路由
@app.route('/search_events', methods=['GET', 'POST'])
def search_events():
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        events = Event.query.filter(Event.name.like(f'%{search_query}%')).all()  # 使用模糊查询
    else:
        events = Event.query.all()  # 默认返回所有事件

    return render_template('search_events.html', events=events)


@app.route('/event_details/<int:event_id>', methods=['GET'])
def event_details(event_id):
    event = Event.query.get(event_id)
    if event:
        event_persons = EventPerson.query.filter_by(event_id=event_id).all()
        persons = []
        for ep in event_persons:
            person = Person.query.get(ep.person_id)
            persons.append({
                'name': person.name,
                'gender': person.gender,
                'birth_date': person.birth_date.strftime('%Y-%m-%d'),
                'death_date': person.death_date.strftime('%Y-%m-%d') if person.death_date else None
            })

        return jsonify({
            'name': event.name,
            'time': event.time.strftime('%Y-%m-%d %H:%M:%S'),
            'process': event.process,
            'effect': event.effect,
            'image_link': event.image_link,
            'persons': persons
        })
    else:
        return jsonify({'error': '事件未找到'}), 404



# 人物查询路由
@app.route('/search_persons', methods=['GET', 'POST'])
def search_persons():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        persons = Person.query.filter(Person.name.contains(search_query)).all()
    else:
        # 如果是GET请求，返回所有人物
        persons = Person.query.all()

    return render_template('search_persons.html', persons=persons)


@app.route('/person_details/<int:person_id>')
def person_details(person_id):
    person = Person.query.get_or_404(person_id)
    person_data = {
        'name': person.name,
        'gender': person.gender,
        'birth_date': person.birth_date.strftime('%Y-%m-%d'),
        'death_date': person.death_date.strftime('%Y-%m-%d') if person.death_date else None,
        'created_at': person.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(person_data)

# 时间查询路由
@app.route('/search_time', methods=['GET', 'POST'])
def search_time():
    if request.method == 'POST':
        year = request.form.get('year')
        if year:
            # 使用extract从事件的时间字段中提取年份进行比较
            events = Event.query.filter(extract('year', Event.time) == int(year)).all()
            return render_template('search_time.html', events=events, years=[])
        else:
            # 没有输入年份时，返回所有事件的发生年份
            events = Event.query.all()
            unique_years = sorted(set(event.time.year for event in events))
            return render_template('search_time.html', years=unique_years, events=events)

    # GET 请求时，默认返回所有事件的年份和所有事件
    events = Event.query.all()
    unique_years = sorted(set(event.time.year for event in events))
    return render_template('search_time.html', years=unique_years, events=events)


# 大模型路由
@app.route('/model')
def model():
    return render_template('model.html')

# 编辑数据路由
@app.route('/edit_data')
def edit_data():
    return render_template('edit_data.html')

@app.route('/')
def index():
    return render_template('index.html', form_type=None)


if __name__ == '__main__':
    app.run(debug=True)
