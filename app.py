from flask import Flask, render_template, request, redirect, make_response
from models import db, User,Section  # 从 models.py 导入数据库和模型
from datetime import datetime
import pytz
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # 初始化数据库连接

# 创建数据库表（只需运行一次）
with app.app_context():
    db.create_all()

# 定义章节类型的顺序
SECTION_ORDER = {
    "网站首页": 1,
    "人物简介": 2,
    "生平事迹": 3,
    "名言名句": 4,
    "邓小平理论": 5
}

# 主页路由
@app.route('/')
def home():
    username = request.cookies.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:  # 如果用户存在
            return redirect('/welcome')
    return render_template('index.html')


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            resp = make_response(redirect('/welcome'))
            resp.set_cookie('username', username)
            return resp
        else:
            return "登录失败，用户名或密码错误"
    return render_template('login.html')


# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']

        new_user = User(username=username, password=password, email=email, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        return "注册成功，您可以<a href='/login'>登录</a>了！"

    return render_template('register.html')


# 忘记密码页面
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']

        user = User.query.filter_by(username=username, email=email, phone=phone).first()
        if user:
            password = user.password
            # send_password_via_email(email, password)  # 发送密码的功能
            return f"已发送密码到 {email}，请查收！"
        else:
            return "用户名、邮箱或手机不匹配，请检查后再试！"

    return render_template('forgot_password.html')


# 欢迎页面
@app.route('/welcome')
def welcome():
    username = request.cookies.get('username')
    if username:
        # 查询所有标题为“网站首页”的章节
        main_sections = Section.query.filter_by(section_title='网站首页').all()
        return render_template('welcome.html', username=username,main_sections=main_sections)
    return redirect('/login')


# 注销
@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.delete_cookie('username')
    return resp

@app.route('/bio')
def bio():
    # 查询所有标题为“人物简介”的章节
    main_sections = Section.query.filter_by(section_title='人物简介').all()
    return render_template('bio.html', main_sections=main_sections)

@app.route('/life_story')
def life_story():
    # 查询所有标题为“生平事迹”的章节
    main_sections = Section.query.filter_by(section_title='生平事迹').all()
    return render_template('life_story.html', main_sections=main_sections)

@app.route('/quotes')
def quotes():
    # 查询所有标题为“名言名句”的章节
    main_sections = Section.query.filter_by(section_title='名言名句').all()
    return render_template('quotes.html', main_sections=main_sections)

@app.route('/theory')
def theory():
    # 查询所有标题为“邓小平理论”的章节
    main_sections = Section.query.filter_by(section_title='邓小平理论').all()
    return render_template('theory.html', main_sections=main_sections)


@app.route('/section/<int:section_id>')
def section_detail(section_id):
    # 根据 ID 查询单个章节
    section = Section.query.get_or_404(section_id)
    return render_template('section_detail.html', section=section)


@app.route('/edit_data', methods=['GET', 'POST'])
def edit_data():
    # 检查用户名是否为 sqy
    username = request.cookies.get('username')
    if username not in ['sqy']:
        return redirect('/welcome')

    if request.method == 'POST':
        # 获取表单数据
        section_id = request.form.get('section_id')
        homepage_content = request.form.get('homepage_content')
        bio_content = request.form.get('bio_content')
        life_story_content = request.form.get('life_story_content')
        quotes_content = request.form.get('quotes_content')
        theory_content = request.form.get('theory_content')

        # 更新或创建对应的Section记录
        def update_or_create_section(title, content, type_, section_id=None):
            if content != '':
                if section_id:
                    # 修改
                    section = Section.query.get(section_id)
                    if section.section_title == title and content is not None:
                        section.section_content = content
                else:
                    # 新增
                    section = Section(
                        section_title=title,
                        section_content=content,
                        type=type_,
                        order=SECTION_ORDER[title],
                        created_at=datetime.now(pytz.timezone('Asia/Shanghai'))
                    )
                    db.session.add(section)
                return section


        # 更新各部分内容
        update_or_create_section("网站首页", homepage_content, "homepage", section_id)
        update_or_create_section("人物简介", bio_content, "bio", section_id)
        update_or_create_section("生平事迹", life_story_content, "life_story", section_id)
        update_or_create_section("名言名句", quotes_content, "quotes", section_id)
        update_or_create_section("邓小平理论", theory_content, "theory", section_id)

        # 提交事务
        db.session.commit()

        # 重定向到编辑页面
        return redirect('/edit_data')

    # 查询数据库中的所有Section记录，按照order升序，然后id升序
    sections = Section.query.order_by(Section.order.asc(), Section.id.asc()).all()

    # 如果是GET请求，则渲染编辑页面
    return render_template('edit_data.html',
                           sections=sections)

# 基础初始化设置
base_url = "http://localhost:11434"
headers = {
    "Content-Type": "application/json"
}
@app.route('/decision_support', methods=['GET', 'POST'])
def decision_support():
    if request.method == 'POST':
        # 获取前端传来的问题
        question = request.form.get('question')
        if not question:
            return render_template('ollama.html', answer="请输入问题后再提交。")

        # 构造请求数据
        prompt = question
        data = {
            "model": "qwen2.5:1.5b",  # 使用的模型名称
            "messages": [{
            "role": "system",
            "content":prompt
            }] ,
            "stream": False,
        }

        # 向 Ollama 发送请求
        try:
            response = requests.post(f"{base_url}/api/chat", headers=headers, json=data)
            result = response.json()
            answer = result.get("message", {}).get("content", "无法生成回答。")
        except Exception as e:
            answer = f"请求失败：{str(e)}"

        # 返回回答到前端
        return render_template('ollama.html', answer=answer)
    else:
        # GET 请求，直接返回表单
        return render_template('ollama.html')

if __name__ == '__main__':
    app.run(debug=True)
