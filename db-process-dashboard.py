import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# 加载环境变量
load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQLHOST'),
        user=os.getenv('MYSQLUSER'),
        password=os.getenv('MYSQLPASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        port=int(os.getenv('MYSQLPORT', 3306))
    )

def drop_old_tables(cursor):
    # 删除旧表
    tables_to_drop = ['dashboard_stats', 'upcoming_games']
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logging.info(f"Dropped table: {table}")
        except Exception as e:
            logging.error(f"Error dropping table {table}: {e}")

def create_page_stats_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            total_page_views INT DEFAULT 0,
            total_predictions INT NOT NULL,
            correct_predictions INT NOT NULL,
            accuracy_rate DECIMAL(5,2) NOT NULL,
            last_update DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    logging.info("Created page_stats table")

def initialize_page_stats(cursor):
    # 检查是否已有记录
    cursor.execute("SELECT COUNT(*) FROM page_stats")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 获取预测统计数据
        cursor.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                SUM(prediction_correct) as correct_predictions
            FROM game_predictions_results 
            WHERE game_status = 3
        """)
        stats = cursor.fetchone()
        
        total_predictions = stats[0]
        correct_predictions = stats[1] or 0
        accuracy_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # 插入初始记录
        cursor.execute("""
            INSERT INTO page_stats 
                (total_page_views, total_predictions, correct_predictions, accuracy_rate, last_update)
            VALUES 
                (0, %s, %s, %s, NOW())
        """, (total_predictions, correct_predictions, accuracy_rate))
        logging.info("Initialized page_stats with default values")

def update_prediction_stats(cursor):
    # 更新预测统计数据
    cursor.execute("""
        SELECT 
            COUNT(*) as total_predictions,
            SUM(prediction_correct) as correct_predictions
        FROM game_predictions_results 
        WHERE game_status = 3
    """)
    stats = cursor.fetchone()
    
    total_predictions = stats[0]
    correct_predictions = stats[1] or 0
    accuracy_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    # 更新统计数据
    cursor.execute("""
        UPDATE page_stats 
        SET total_predictions = %s,
            correct_predictions = %s,
            accuracy_rate = %s,
            last_update = NOW()
        WHERE id = 1
    """, (total_predictions, correct_predictions, accuracy_rate))
    logging.info("Updated prediction statistics")

def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 删除旧表
        drop_old_tables(cursor)
        
        # 创建新表
        create_page_stats_table(cursor)
        
        # 初始化数据
        initialize_page_stats(cursor)
        
        # 更新预测统计
        update_prediction_stats(cursor)
        
        # 提交更改
        conn.commit()
        logging.info("Page statistics updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating page statistics: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 