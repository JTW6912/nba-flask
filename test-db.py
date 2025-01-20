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
            port=int(os.getenv('MYSQLPORT'))
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"成功连接到MySQL数据库。服务器版本: {db_info}")
            
            cursor = connection.cursor()
            
            # 查看 game_predictions_results 表
            logger.info("\n查看 game_predictions_results 表:")
            try:
                cursor.execute("SELECT * FROM game_predictions_results LIMIT 5")
                results = cursor.fetchall()
                if results:
                    # 获取列名
                    column_names = [i[0] for i in cursor.description]
                    logger.info(f"列名: {column_names}")
                    for row in results:
                        logger.info(row)
                else:
                    logger.info("game_predictions_results 表为空")
            except Error as e:
                logger.error(f"查询 game_predictions_results 表时出错: {e}")
            
            # 查看 teams 表
            logger.info("\n查看 teams 表:")
            try:
                cursor.execute("SELECT * FROM teams LIMIT 5")
                results = cursor.fetchall()
                if results:
                    # 获取列名
                    column_names = [i[0] for i in cursor.description]
                    logger.info(f"列名: {column_names}")
                    for row in results:
                        logger.info(row)
                else:
                    logger.info("teams 表为空")
            except Error as e:
                logger.error(f"查询 teams 表时出错: {e}")
            
            cursor.close()
            connection.close()
            logger.info("\n数据库连接已关闭")
            return True

    except Error as e:
        logger.error(f"连接数据库时出错: {e}")
        return False

if __name__ == "__main__":
    if test_database_connection():
        logger.info("数据库连接测试成功！")
    else:
        logger.error("数据库连接测试失败！") 