from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:20040707sqy@localhost:3306/dxp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 用户表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 密码不加密
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Enum('管理员', '会员', '游客', name='user_roles'), nullable=False, default='游客')
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))

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

        # 创建新用户并保存到数据库
        new_user = User(username=username, password=password, email=email, phone=phone, role=role)  # 明文存储密码
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
        user = User.query.filter_by(username=username, password=password).first()  # 明文验证密码
        if user:
            flash('登录成功！', 'success')
            return redirect(url_for('index'))  # 登录后重定向到首页
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


@app.route('/')
def index():
    return render_template('index.html', form_type=None)


if __name__ == '__main__':
    app.run(debug=True)
