from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import json
import uuid
import pandas as pd
import io
import os
from tempfile import NamedTemporaryFile

app = Flask(__name__)
# 从环境变量获取数据库配置，如果不存在则使用默认值
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', 'mysqlpass')
db_host = os.environ.get('DB_HOST', '1.92.146.109')
db_name = os.environ.get('DB_NAME', 'Classhelper')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 从环境变量获取密钥，提高安全性
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '8208231325_jike2308_secret_key')
db = SQLAlchemy(app)

# 管理员角色枚举
ROLE_ADMIN = 1       # 普通管理员
ROLE_SUPER_ADMIN = 2  # 超级管理员

# 定义管理员模型
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # 修改为256长度
    role = db.Column(db.Integer, default=ROLE_ADMIN)  # 1=普通管理员, 2=超级管理员
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 定义表单模型
class Form(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    questions = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)  # 关联创建者
    
# 添加一个新的模型用于存储用户信息
class UserInfo(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    qq_number = db.Column(db.String(15), nullable=True)  # QQ号
    nickname = db.Column(db.String(50), nullable=True)   # 昵称
    class_number = db.Column(db.String(20), nullable=True)  # 班级号
    student_id = db.Column(db.String(20), nullable=True)   # 学号
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 修改Response模型，添加用户信息关联
class Response(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    form_id = db.Column(db.String(36), db.ForeignKey('form.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    user_info_id = db.Column(db.String(36), db.ForeignKey('user_info.id'), nullable=True)  # 关联用户信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系映射
    user_info = db.relationship('UserInfo', backref='responses')

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# 超级管理员验证装饰器
def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin or admin.role != ROLE_SUPER_ADMIN:
            flash('需要超级管理员权限', 'danger')
            return redirect(url_for('admin_dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

# 首页
@app.route('/')
def index():
    forms = Form.query.all()
    return render_template('index.html', forms=forms)

# 管理员登录页面
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_role'] = admin.role
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('admin/login.html')

# 管理员退出登录
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin_login'))

# 管理员仪表板
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    admin_id = session.get('admin_id')
    admin = Admin.query.get(admin_id)
    forms = Form.query.filter_by(admin_id=admin_id).all()
    
    return render_template('admin/dashboard.html', admin=admin, forms=forms)

# 管理员管理
@app.route('/admin/manage')
@super_admin_required
def admin_manage():
    admins = Admin.query.all()
    return render_template('admin/manage_admins.html', admins=admins)

# 添加管理员
@app.route('/admin/add', methods=['GET', 'POST'])
@super_admin_required
def admin_add():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = int(request.form.get('role', ROLE_ADMIN))
        
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('用户名已存在', 'danger')
            return redirect(url_for('admin_add'))
        
        new_admin = Admin(username=username, role=role)
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('管理员已添加成功', 'success')
        return redirect(url_for('admin_manage'))
    
    return render_template('admin/add_admin.html')

# 删除管理员
@app.route('/admin/delete/<int:admin_id>', methods=['POST'])
@super_admin_required
def admin_delete(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # 不能删除自己
    if admin_id == session.get('admin_id'):
        flash('不能删除自己的账号', 'danger')
        return redirect(url_for('admin_manage'))
    
    db.session.delete(admin)
    db.session.commit()
    
    flash('管理员已删除', 'success')
    return redirect(url_for('admin_manage'))

# 创建表单页面 (仅管理员)
@app.route('/create_form')
@login_required
def create_form():
    template_id = request.args.get('template_id')
    template_data = None
    
    if template_id:
        template = Form.query.get(template_id)
        if template:
            # 检查权限
            admin_id = session.get('admin_id')
            if template.admin_id == admin_id or session.get('admin_role') == ROLE_SUPER_ADMIN:
                template_data = {
                    'id': template.id,
                    'title': template.title,
                    'description': template.description,
                    'questions': json.loads(template.questions)
                }
    
    return render_template('create_form.html', template=template_data)

# 处理创建表单请求 (仅管理员)
@app.route('/api/forms', methods=['POST'])
@login_required
def api_create_form():
    data = request.json
    form_id = str(uuid.uuid4())
    admin_id = session.get('admin_id')
    
    new_form = Form(
        id=form_id,
        title=data['title'],
        description=data.get('description', ''),
        questions=json.dumps(data['questions']),
        admin_id=admin_id
    )
    db.session.add(new_form)
    db.session.commit()
    return jsonify({'success': True, 'form_id': form_id})

# 查看表单 (所有人可见)
@app.route('/form/<form_id>')
def view_form(form_id):
    form = Form.query.get_or_404(form_id)
    questions = json.loads(form.questions)
    return render_template('view_form.html', form=form, questions=questions)

# 修改提交表单回答API来支持用户信息
@app.route('/api/submit/<form_id>', methods=['POST'])
def submit_form(form_id):
    data = request.json
    answers_data = data.get('answers', data)  # 兼容新旧格式
    user_info_data = data.get('user_info')
    
    response_id = str(uuid.uuid4())
    user_info_id = None
    
    # 如果提供了用户信息，先保存用户信息
    if user_info_data:
        user_info_id = str(uuid.uuid4())
        new_user_info = UserInfo(
            id=user_info_id,
            qq_number=user_info_data.get('qq_number'),
            nickname=user_info_data.get('nickname'),
            class_number=user_info_data.get('class_number'),
            student_id=user_info_data.get('student_id')
        )
        db.session.add(new_user_info)
    
    # 保存回答
    new_response = Response(
        id=response_id,
        form_id=form_id,
        answers=json.dumps(answers_data),
        user_info_id=user_info_id
    )
    db.session.add(new_response)
    db.session.commit()
    
    # 在会话中存储用户提交的表单ID列表
    if 'my_responses' not in session:
        session['my_responses'] = []
    
    # 将新提交的表单回答加入到用户的提交列表中
    my_responses = session['my_responses']
    my_responses.append(response_id)
    session['my_responses'] = my_responses
    
    return jsonify({'success': True, 'response_id': response_id})

# 查看表单结果 (仅管理员)
@app.route('/results/<form_id>')
@login_required
def view_results(form_id):
    form = Form.query.get_or_404(form_id)
    
    # 检查访问权限
    if form.admin_id != session.get('admin_id') and session.get('admin_role') != ROLE_SUPER_ADMIN:
        flash('无权访问此表单结果', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    responses = Response.query.filter_by(form_id=form_id).all()
    
    questions = json.loads(form.questions)
    answers_list = []
    user_info_list = []
    
    for response in responses:
        answers_list.append(json.loads(response.answers))
        # 添加用户信息
        if response.user_info:
            user_info_list.append({
                'qq_number': response.user_info.qq_number,
                'nickname': response.user_info.nickname,
                'class_number': response.user_info.class_number,
                'student_id': response.user_info.student_id,
                'created_at': response.created_at
            })
        else:
            user_info_list.append(None)
    
    return render_template('results.html', form=form, questions=questions, answers=answers_list, user_info_list=user_info_list)

# 导出为Excel (仅管理员)
@app.route('/export/<form_id>')
@login_required
def export_excel(form_id):
    form = Form.query.get_or_404(form_id)
    
    # 检查访问权限
    if form.admin_id != session.get('admin_id') and session.get('admin_role') != ROLE_SUPER_ADMIN:
        flash('无权导出此表单结果', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    responses = Response.query.filter_by(form_id=form_id).all()
    
    questions = json.loads(form.questions)
    
    # 准备数据
    data = []
    columns = ['序号', 'QQ号', '昵称', '班级', '学号']  # 添加用户信息列
    
    # 添加问题作为列名
    for question in questions:
        columns.append(question['title'])
    columns.append('提交时间')
    
    # 添加回答数据
    for i, response in enumerate(responses):
        answers = json.loads(response.answers)
        row = [i + 1]  # 序号
        
        # 添加用户信息
        if response.user_info:
            row.append(response.user_info.qq_number or '')
            row.append(response.user_info.nickname or '')
            row.append(response.user_info.class_number or '')
            row.append(response.user_info.student_id or '')
        else:
            row.extend(['', '', '', ''])  # 没有用户信息则添加空值
        
        # 添加每个问题的回答
        for j, question in enumerate(questions):
            answer = answers[j]['answer']
            
            # 处理不同类型的答案
            if answer is None:
                row.append('')
            elif isinstance(answer, list):
                row.append(', '.join(answer))
            else:
                row.append(answer)
        
        # 添加提交时间
        row.append(response.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        
        data.append(row)
    
    # 创建DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    # 创建一个临时文件用于保存Excel
    with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        # 创建一个Excel写入器
        writer = pd.ExcelWriter(tmp.name, engine='openpyxl')
        
        # 写入数据表
        df.to_excel(writer, sheet_name='回答数据', index=False)
        
        # 如果有选择题，为每个选择题创建一个统计表
        for i, question in enumerate(questions):
            if question['type'] in ['radio', 'checkbox']:
                stats_data = []
                stats_columns = ['选项', '数量', '百分比']
                
                options = question['options']
                for option in options:
                    count = 0
                    for response in responses:
                        answer = json.loads(response.answers)[i]['answer']
                        if question['type'] == 'radio' and answer == option:
                            count += 1
                        elif question['type'] == 'checkbox' and answer and option in answer:
                            count += 1
                    
                    percentage = 0 if len(responses) == 0 else round(count / len(responses) * 100, 1)
                    stats_data.append([option, count, f"{percentage}%"])
                
                stats_df = pd.DataFrame(stats_data, columns=stats_columns)
                stats_df.to_excel(writer, sheet_name=f'问题{i+1}统计', index=False)
        
        # 保存Excel
        writer.close()
        
        # 获取临时文件的名称
        temp_filename = tmp.name
    
    # 发送文件
    response = send_file(
        temp_filename,
        as_attachment=True,
        download_name=f"{form.title}_统计结果_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # 文件发送后删除临时文件
    @response.call_on_close
    def remove_file():
        try:
            os.unlink(temp_filename)
        except:
            pass
    
    return response

# 检测QQ分享信息并重定向到表单
@app.route('/qqshare/<form_id>')
def qq_share_redirect(form_id):
    # 获取QQ Web分享的参数
    qq_number = request.args.get('qq', '')
    nickname = request.args.get('nickname', '')
    
    # 重定向到表单，附加QQ信息参数
    redirect_url = url_for('view_form', form_id=form_id)
    if qq_number or nickname:
        redirect_url += f'?qq={qq_number}&nickname={nickname}'
    
    return redirect(redirect_url)

# 用户查看自己的提交记录
@app.route('/my-responses')
def my_responses():
    # 从会话中获取用户提交的表单ID
    response_ids = session.get('my_responses', [])
    
    # 获取用户的所有提交记录
    responses = []
    if response_ids:
        for response_id in response_ids:
            response = Response.query.get(response_id)
            if response:
                form = Form.query.get(response.form_id)
                if form:
                    responses.append({
                        'id': response.id,
                        'form_id': response.form_id,
                        'form_title': form.title,
                        'created_at': response.created_at
                    })
    
    return render_template('my_responses.html', responses=responses)

# 查看自己的回答详情
@app.route('/response/<response_id>')
def view_response(response_id):
    # 验证是否是用户自己的提交
    my_responses = session.get('my_responses', [])
    if response_id not in my_responses:
        flash('您无权查看此回答', 'danger')
        return redirect(url_for('index'))
    
    response = Response.query.get_or_404(response_id)
    form = Form.query.get_or_404(response.form_id)
    
    questions = json.loads(form.questions)
    answers = json.loads(response.answers)
    
    user_info = None
    if response.user_info_id:
        user_info = UserInfo.query.get(response.user_info_id)
    
    return render_template('view_response.html', 
                          response=response, 
                          form=form, 
                          questions=questions, 
                          answers=answers, 
                          user_info=user_info,
                          zip=zip)

# 修改自己的回答
@app.route('/edit-response/<response_id>')
def edit_response(response_id):
    # 验证是否是用户自己的提交
    my_responses = session.get('my_responses', [])
    if response_id not in my_responses:
        flash('您无权修改此回答', 'danger')
        return redirect(url_for('index'))
    
    response = Response.query.get_or_404(response_id)
    form = Form.query.get_or_404(response.form_id)
    
    questions = json.loads(form.questions)
    answers = json.loads(response.answers)
    
    user_info = None
    if response.user_info_id:
        user_info = UserInfo.query.get(response.user_info_id)
    
    return render_template('edit_response.html', 
                          response=response, 
                          form=form, 
                          questions=questions, 
                          answers=answers, 
                          user_info=user_info,
                          zip=zip)

# 处理修改回答的API
@app.route('/api/update-response/<response_id>', methods=['POST'])
def update_response(response_id):
    # 验证是否是用户自己的提交
    my_responses = session.get('my_responses', [])
    if response_id not in my_responses:
        return jsonify({'success': False, 'message': '您无权修改此回答'}), 403
    
    data = request.json
    answers_data = data.get('answers', [])
    user_info_data = data.get('user_info')
    
    response = Response.query.get_or_404(response_id)
    
    # 更新回答
    response.answers = json.dumps(answers_data)
    
    # 如果提供了用户信息且原来有用户信息，则更新
    if user_info_data and response.user_info_id:
        user_info = UserInfo.query.get(response.user_info_id)
        if user_info:
            user_info.qq_number = user_info_data.get('qq_number', user_info.qq_number)
            user_info.nickname = user_info_data.get('nickname', user_info.nickname)
            user_info.class_number = user_info_data.get('class_number', user_info.class_number)
            user_info.student_id = user_info_data.get('student_id', user_info.student_id)
    # 如果提供了用户信息但原来没有，则创建新的
    elif user_info_data and not response.user_info_id:
        user_info_id = str(uuid.uuid4())
        new_user_info = UserInfo(
            id=user_info_id,
            qq_number=user_info_data.get('qq_number'),
            nickname=user_info_data.get('nickname'),
            class_number=user_info_data.get('class_number'),
            student_id=user_info_data.get('student_id')
        )
        db.session.add(new_user_info)
        response.user_info_id = user_info_id
    
    db.session.commit()
    
    return jsonify({'success': True})

# 删除自己的回答
@app.route('/api/delete-response/<response_id>', methods=['POST'])
def delete_response(response_id):
    # 验证是否是用户自己的提交
    my_responses = session.get('my_responses', [])
    if response_id not in my_responses:
        return jsonify({'success': False, 'message': '您无权删除此回答'}), 403
    
    response = Response.query.get_or_404(response_id)
    
    # 如果存在用户信息，也删除用户信息
    if response.user_info_id:
        user_info = UserInfo.query.get(response.user_info_id)
        if user_info:
            db.session.delete(user_info)
    
    # 删除回答
    db.session.delete(response)
    db.session.commit()
    
    # 从会话中移除此回答ID
    my_responses.remove(response_id)
    session['my_responses'] = my_responses
    
    return jsonify({'success': True})

# 添加复制表单为模板的API
@app.route('/api/duplicate_form/<form_id>', methods=['POST'])
@login_required
def duplicate_form(form_id):
    # 获取原始表单
    original_form = Form.query.get_or_404(form_id)
    admin_id = session.get('admin_id')
    
    # 检查访问权限
    if original_form.admin_id != admin_id and session.get('admin_role') != ROLE_SUPER_ADMIN:
        return jsonify({'success': False, 'message': '无权复制此表单'}), 403
    
    # 创建新表单
    new_form_id = str(uuid.uuid4())
    new_title = request.json.get('title', f"{original_form.title} - 副本")
    
    new_form = Form(
        id=new_form_id,
        title=new_title,
        description=original_form.description,
        questions=original_form.questions,  # 直接复制问题结构
        admin_id=admin_id
    )
    
    db.session.add(new_form)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'form_id': new_form_id,
        'redirect_url': url_for('create_form') + f'?template_id={new_form_id}'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 创建初始超级管理员账号
        admin = Admin.query.filter_by(username='8208231325').first()
        if not admin:
            super_admin = Admin(username='8208231325', role=ROLE_SUPER_ADMIN)
            super_admin.set_password('jike2308')
            db.session.add(super_admin)
            db.session.commit()
            print("已创建超级管理员账号：8208231325")
    
    # 从环境变量获取主机和端口配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 2308))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 