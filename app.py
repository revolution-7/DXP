from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField
from wtforms.validators import DataRequired, Email, Length

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:20040707sqy@localhost:3306/dxp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sqy'  # 用于表单加密的密钥

db = SQLAlchemy(app)


# 用户表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Enum('管理员', '会员', '游客', name='user_roles'), nullable=False, default='游客')
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# 表单类
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=1, max=80)])
    password = PasswordField('密码', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=1, max=80)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    phone = StringField('电话', validators=[DataRequired()])
    role = SelectField('角色', choices=[('游客', '游客'), ('会员', '会员'), ('管理员', '管理员')], default='游客')


class ResetPasswordForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    phone = StringField('电话', validators=[DataRequired()])


# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        phone = form.phone.data
        role = form.role.data

        # 检查用户名或电话是否已存在
        user = User.query.filter((User.username == username) | (User.phone == phone) | (User.email == email)).first()
        if user:
            flash('用户名、邮箱或电话已存在！')
            return redirect(url_for('register'))

        # 创建新用户并保存到数据库
        new_user = User(username=username, email=email, phone=phone, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录！')
        return redirect(url_for('index'))
    return render_template('index.html', form=form)


# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash('登录成功！')
            return redirect(url_for('index'))  # 登录后重定向到首页
        else:
            flash('用户名或密码错误！')
            return redirect(url_for('login'))

    return render_template('index.html', form=form)


# 找回密码
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        phone = form.phone.data

        # 查找用户
        user = User.query.filter_by(username=username, email=email, phone=phone).first()
        if user:
            # 处理密码重置逻辑（这里只是示范，可以生成一个token或发送邮件）
            flash('验证通过，请检查您的邮箱进行密码重置！')
            return redirect(url_for('index'))
        else:
            flash('用户信息不匹配！')
            return redirect(url_for('reset_password'))

    return render_template('index.html', form=form)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
