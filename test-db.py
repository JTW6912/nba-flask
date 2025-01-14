import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    # 加载环境变量
    load_dotenv()
    
    try:
        # 尝试连接数据库
        logger.info("正在连接数据库...")
        connection = mysql.connector.connect(
            host=os.getenv('MYSQLHOST'),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
            port=os.getenv('MYSQLPORT')
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"成功连接到MySQL数据库。服务器版本: {db_info}")
            
            # 创建游标并执行测试查询
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()[0]
            logger.info(f"当前数据库名称: {database_name}")
            
            cursor.close()
            connection.close()
            logger.info("数据库连接已关闭")
            return True

    except Error as e:
        logger.error(f"连接数据库时出错: {e}")
        return False

if __name__ == "__main__":
    if test_database_connection():
        logger.info("数据库连接测试成功！")
    else:
        logger.error("数据库连接测试失败！") 