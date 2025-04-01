# 收集表系统

一个现代化、易用的表单收集和管理系统，支持多种问题类型、数据导出和团队协作。

## 功能特点

- 创建各种类型的表单（文本、单选、多选等）
- 使用模板快速创建新表单
- 实时保存用户回答
- 导出数据为Excel格式
- 多级管理员权限控制
- 响应式设计，支持各种设备

## 技术栈

- 后端: Flask, SQLAlchemy
- 前端: Bootstrap 5, JavaScript
- 数据库: MySQL

## 安装和部署

### 前提条件

- Python 3.8+
- MySQL 数据库

### 本地开发环境设置

1. 克隆项目仓库:
   ```
   git clone <repository-url>
   cd Classhelper
   ```

2. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

3. 配置环境变量:
   ```
   # 复制示例环境变量文件
   cp .env.example .env
   # 编辑.env文件设置你的数据库和应用配置
   ```

4. 初始化数据库:
   ```
   python app.py
   ```

5. 启动开发服务器:
   ```
   python app.py
   ```

### 生产环境部署

#### 使用Gunicorn部署

1. 安装Gunicorn:
   ```
   pip install gunicorn
   ```

2. 启动应用:
   ```
   gunicorn --bind 0.0.0.0:2308 wsgi:app
   ```

#### 使用Docker部署

1. 构建Docker镜像:
   ```
   docker build -t classhelper .
   ```

2. 运行容器:
   ```
   docker run -d -p 2308:2308 \
     -e DB_USER=your_db_user \
     -e DB_PASSWORD=your_db_password \
     -e DB_HOST=your_db_host \
     -e DB_NAME=your_db_name \
     -e SECRET_KEY=your_secret_key \
     --name classhelper classhelper
   ```

## 默认管理员账号

系统初始化时会自动创建超级管理员账号:
- 用户名: 8208231325
- 密码: jike2308

**重要**: 首次登录后请立即修改默认密码!

## 许可证

© 2024 收集表系统 | 轻松创建、收集和分析表单数据 