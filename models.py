from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# 定义用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)

class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    section_title = db.Column(db.String(200), nullable=False)  # 章节标题
    section_content = db.Column(db.Text, nullable=True)  # 内容可以为空
    image_path = db.Column(db.String(300), nullable=True)  # 新增字段，存储图片路径
    parent_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)  # 父章节
    order = db.Column(db.Integer, nullable=False)  # 章节顺序
    type = db.Column(db.String(50), nullable=False)  # 标识板块类型 (bio, life_story, etc.)
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Shanghai')))
    # 关联父章节
    parent = db.relationship('Section', remote_side=[id], backref='subsections')