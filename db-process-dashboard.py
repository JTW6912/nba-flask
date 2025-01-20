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

def create_dashboard_stats_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            total_predictions INT NOT NULL,
            correct_predictions INT NOT NULL,
            accuracy_rate DECIMAL(5,2) NOT NULL,
            last_update DATETIME NOT NULL,
            page_views INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

def create_upcoming_games_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upcoming_games (
            id INT AUTO_INCREMENT PRIMARY KEY,
            game_id VARCHAR(20) NOT NULL,
            game_date DATE NOT NULL,
            home_team_id INT NOT NULL,
            away_team_id INT NOT NULL,
            home_team_name VARCHAR(100) NOT NULL,
            away_team_name VARCHAR(100) NOT NULL,
            home_win_probability_logistic DECIMAL(6,4) NOT NULL,
            away_win_probability_logistic DECIMAL(6,4) NOT NULL,
            home_win_probability_rf DECIMAL(6,4) NOT NULL,
            away_win_probability_rf DECIMAL(6,4) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

def update_dashboard_stats(cursor):
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
    
    # 更新或插入统计数据
    cursor.execute("""
        INSERT INTO dashboard_stats 
            (total_predictions, correct_predictions, accuracy_rate, last_update, page_views)
        VALUES 
            (%s, %s, %s, NOW(), 0)
        ON DUPLICATE KEY UPDATE
            total_predictions = VALUES(total_predictions),
            correct_predictions = VALUES(correct_predictions),
            accuracy_rate = VALUES(accuracy_rate),
            last_update = NOW()
    """, (total_predictions, correct_predictions, accuracy_rate))

def update_upcoming_games(cursor):
    # 清除旧的upcoming games数据
    cursor.execute("TRUNCATE TABLE upcoming_games")
    
    # 获取未来5场比赛的预测（基于当前系统时间）
    cursor.execute("""
        SELECT 
            gpr.game_id,
            gpr.game_date,
            gpr.home_team_id,
            gpr.away_team_id,
            ht.team_name as home_team_name,
            at.team_name as away_team_name,
            gpr.home_win_probability_logistic,
            gpr.away_win_probability_logistic,
            gpr.home_win_probability_rf,
            gpr.away_win_probability_rf
        FROM game_predictions_results gpr
        JOIN teams ht ON gpr.home_team_id = ht.team_id
        JOIN teams at ON gpr.away_team_id = at.team_id
        WHERE gpr.game_date >= CURDATE()
            AND gpr.game_status = 1  -- 1表示比赛未开始
        ORDER BY gpr.game_date ASC, gpr.game_id ASC
        LIMIT 5
    """)
    
    upcoming_games = cursor.fetchall()
    
    # 插入新的upcoming games数据
    for game in upcoming_games:
        cursor.execute("""
            INSERT INTO upcoming_games (
                game_id, game_date, home_team_id, away_team_id,
                home_team_name, away_team_name,
                home_win_probability_logistic, away_win_probability_logistic,
                home_win_probability_rf, away_win_probability_rf
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, game)
        
    # 记录更新的比赛数量
    logging.info(f"Updated {len(upcoming_games)} upcoming games")
    
    # 如果没有找到未来比赛，记录警告
    if not upcoming_games:
        logging.warning("No upcoming games found in the database")

def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建所需的表
        create_dashboard_stats_table(cursor)
        create_upcoming_games_table(cursor)
        
        # 更新数据
        update_dashboard_stats(cursor)
        update_upcoming_games(cursor)
        
        # 提交更改
        conn.commit()
        logging.info("Dashboard data updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating dashboard data: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 