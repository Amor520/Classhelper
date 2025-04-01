from app import app, db

# 在应用上下文中执行数据库操作
with app.app_context():
    print("正在删除所有表...")
    db.drop_all()
    
    print("正在创建所有表...")
    db.create_all()
    
    print("数据库迁移完成！")
    print("注意：所有数据已被清除。如果需要，请重新导入或创建数据。") 