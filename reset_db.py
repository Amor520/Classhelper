from app import app, db

with app.app_context():
    db.drop_all()
    db.create_all()
    print("数据库表已重新创建") 