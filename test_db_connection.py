import os
from app import app, db, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    try:
        with app.app_context():
            # 测试 1: 创建表
            logger.info("Testing database connection...")
            db.create_all()
            logger.info("✅ Database tables created successfully")

            # 测试 2: 添加测试用户
            test_username = "test_user"
            test_user = User.query.filter_by(username=test_username).first()
            if test_user:
                db.session.delete(test_user)
                db.session.commit()
            
            new_user = User(username=test_username)
            new_user.set_password("test123")
            db.session.add(new_user)
            db.session.commit()
            logger.info("✅ Test user created successfully")

            # 测试 3: 查询用户
            user = User.query.filter_by(username=test_username).first()
            if user:
                logger.info("✅ User query successful")
            else:
                logger.error("❌ User query failed")

            # 测试 4: 删除测试用户
            db.session.delete(user)
            db.session.commit()
            logger.info("✅ Test user deleted successfully")

            logger.info("All database tests passed successfully! ✨")
            return True

    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_database_connection() 