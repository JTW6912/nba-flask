from app import db, User, app
from sqlalchemy.exc import SQLAlchemyError

def test_database_connection():
    try:
        with app.app_context():
            # 尝试创建数据库表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 尝试创建测试用户
            test_user = User(
                username="test_user",
                email="test@example.com"
            )
            test_user.set_password("test123")
            
            # 添加并提交到数据库
            db.session.add(test_user)
            db.session.commit()
            print("✅ 测试用户创建成功")
            
            # 查询测试用户
            queried_user = User.query.filter_by(username="test_user").first()
            if queried_user and queried_user.email == "test@example.com":
                print("✅ 数据库查询成功")
            
            # 清理测试数据
            db.session.delete(queried_user)
            db.session.commit()
            print("✅ 测试数据清理成功")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ 数据库错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试数据库连接...")
    success = test_database_connection()
    if success:
        print("✅ 数据库连接测试完成：所有测试通过")
    else:
        print("❌ 数据库连接测试失败") 