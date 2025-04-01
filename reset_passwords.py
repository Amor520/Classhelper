from app import app, db, Admin
from werkzeug.security import generate_password_hash

# 默认管理员密码
DEFAULT_PASSWORD = 'jike2308'

def reset_all_admin_passwords():
    with app.app_context():
        # 获取所有管理员账户
        admins = Admin.query.all()
        
        # 重置每个管理员的密码
        for admin in admins:
            print(f"正在重置管理员 {admin.username} 的密码...")
            admin.password_hash = generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256')
        
        # 提交更改
        db.session.commit()
        print(f"已成功重置 {len(admins)} 个管理员账户的密码为 '{DEFAULT_PASSWORD}'")

if __name__ == '__main__':
    reset_all_admin_passwords() 