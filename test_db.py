import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQLHOST'),
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQLPASSWORD'),
            database=os.environ.get('MYSQL_DATABASE'),
            port=int(os.environ.get('MYSQLPORT', '3306'))
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise

def main():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if tables exist
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\nAvailable tables:")
            for table in tables:
                print(f"- {list(table.values())[0]}")
            
            # Check game_predictions_results table structure
            print("\nChecking game_predictions_results table structure:")
            cursor.execute("DESCRIBE game_predictions_results")
            columns = cursor.fetchall()
            for column in columns:
                print(f"- {column['Field']}: {column['Type']}")
            
            # Check if there's any data in game_predictions_results
            print("\nChecking game_predictions_results data:")
            cursor.execute("SELECT COUNT(*) as count FROM game_predictions_results")
            count = cursor.fetchone()['count']
            print(f"Total records: {count}")
            
            if count > 0:
                # Show a sample of records
                print("\nSample records from game_predictions_results:")
                cursor.execute("""
                    SELECT 
                        gpr.*,
                        ht.team_name as home_team,
                        at.team_name as away_team
                    FROM game_predictions_results gpr
                    JOIN teams ht ON gpr.home_team_id = ht.team_id
                    JOIN teams at ON gpr.away_team_id = at.team_id
                    LIMIT 3
                """)
                records = cursor.fetchall()
                for record in records:
                    print("\nGame Record:")
                    print(f"- Date: {record['game_date']}")
                    print(f"- Teams: {record['home_team']} vs {record['away_team']}")
                    print(f"- Score: {record['home_team_score']} - {record['away_team_score']}")
                    print(f"- Predictions: LR={record['lr_home_win_prob']:.2f}, RF={record['rf_home_win_prob']:.2f}")
            else:
                print("No records found in game_predictions_results table")
            
            # Check teams table
            print("\nChecking teams table:")
            cursor.execute("SELECT COUNT(*) as count FROM teams")
            teams_count = cursor.fetchone()['count']
            print(f"Total teams: {teams_count}")
            
            if teams_count > 0:
                print("\nSample teams:")
                cursor.execute("SELECT * FROM teams LIMIT 5")
                teams = cursor.fetchall()
                for team in teams:
                    print(f"- {team['team_name']} (ID: {team['team_id']})")

    except Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 