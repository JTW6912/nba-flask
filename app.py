from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from sqlalchemy import text
import traceback
import time
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

# 数据库配置部分
def get_database_url():
    config = {
        'user': os.environ.get('MYSQLUSER', 'root'),
        'password': os.environ.get('MYSQLPASSWORD'),
        'host': os.environ.get('MYSQLHOST'),
        'port': os.environ.get('MYSQLPORT', '3306'),
        'database': os.environ.get('MYSQL_DATABASE')
    }
    
    # 验证必要的配置
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required MySQL environment variables: {', '.join(missing)}")
    
    return f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

def configure_database(app):
    # 数据库配置
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': int(os.environ.get('MAX_POOL_SIZE', '5')),
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 60,
            'use_pure': True
        }
    }
    return SQLAlchemy(app)

try:
    # 配置并初始化数据库
    db = configure_database(app)
    print("Database configuration completed")
except Exception as e:
    print(f"Failed to configure database: {str(e)}")
    raise

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
        app.logger.error(f"Error connecting to MySQL: {e}")
        raise

def check_db_connection():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            db.session.execute(text('SELECT 1')).fetchone()
            return True
        except Exception as e:
            retry_count += 1
            app.logger.error(f"Database connection attempt {retry_count} failed: {str(e)}")
            if retry_count == max_retries:
                app.logger.error("Max retries reached, database connection failed")
                return False
            db.session.remove()
            time.sleep(1)  # 等待1秒后重试
    return False

@app.before_request
def before_request():
    if not check_db_connection():
        return jsonify({"error": "Database connection failed"}), 503

@app.teardown_request
def teardown_request(exception=None):
    if exception:
        app.logger.error(f"Request error: {str(exception)}")
        db.session.rollback()
    db.session.remove()

def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database initialization failed: {str(e)}")
            raise

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    try:
        print("Accessing index page")
        return render_template('index.html')
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('register.html', form=form)
            
            # 创建新用户
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            print(f"New user registered: {user.username}")
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error in registration: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html', form=form)
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                print(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            print(f"Failed login attempt for username: {username}")
            flash('Invalid username or password')
        return render_template('login.html')
    except Exception as e:
        print(f"Error in login route: {str(e)}")
        return jsonify({"error": str(e)}), 500

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取仪表盘统计数据
        cursor.execute("SELECT * FROM dashboard_stats ORDER BY id DESC LIMIT 1")
        stats = cursor.fetchone()
        
        if not stats:
            # 如果没有统计数据，创建初始数据
            cursor.execute("""
                INSERT INTO dashboard_stats 
                (total_predictions, correct_predictions, accuracy_rate, last_update, page_views)
                VALUES (0, 0, 0.0, NOW(), 0)
            """)
            conn.commit()
            cursor.execute("SELECT * FROM dashboard_stats ORDER BY id DESC LIMIT 1")
            stats = cursor.fetchone()
        
        # 获取即将到来的比赛
        cursor.execute("""
            SELECT * FROM upcoming_games 
            ORDER BY game_date ASC 
            LIMIT 5
        """)
        upcoming_games = cursor.fetchall()
        
        # 更新页面浏览量
        cursor.execute("""
            UPDATE dashboard_stats 
            SET page_views = page_views + 1,
                last_update = NOW()
            WHERE id = %s
        """, (stats['id'],))
        stats['page_views'] += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             upcoming_games=upcoming_games)
                             
    except Exception as e:
        app.logger.error(f"Error in dashboard route: {str(e)}")
        app.logger.error(traceback.format_exc())  # 添加详细的错误跟踪
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        flash("An error occurred while loading the dashboard", "error")
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    try:
        username = current_user.username
        logout_user()
        print(f"User {username} logged out")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error in logout route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict')
def predict():
    try:
        # Get pagination and sorting parameters
        page = request.args.get('page', 1, type=int)
        sort_order = request.args.get('sort', 'asc')
        date_filter = request.args.get('date_filter', 'all')
        start_date = request.args.get('start_date')
        
        per_page = 10
        offset = (page - 1) * per_page

        # Build date filter condition
        date_condition = ""
        query_params = []
        today = datetime.now().date()
        
        if date_filter == '7d':
            date_condition = "AND game_date BETWEEN %s AND %s"
            query_params = [today, today + timedelta(days=7)]
        elif date_filter == '30d':
            date_condition = "AND game_date BETWEEN %s AND %s"
            query_params = [today, today + timedelta(days=30)]
        elif date_filter == '1y':
            date_condition = "AND game_date BETWEEN %s AND %s"
            query_params = [today, today + timedelta(days=365)]
        elif date_filter == 'custom' and start_date:
            try:
                custom_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                date_condition = "AND game_date = %s"
                query_params = [custom_date]
            except ValueError:
                app.logger.error(f"Invalid date format: {start_date}")
                return render_template('error.html', error="Invalid date format. Please use YYYY-MM-DD")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Get total count
            count_query = f'SELECT COUNT(*) as count FROM game_predictions_results WHERE 1=1 {date_condition}'
            cursor.execute(count_query, query_params)
            total_records = cursor.fetchone()['count']
            total_pages = (total_records + per_page - 1) // per_page

            # Get predictions
            query = '''
                SELECT 
                    gpr.id,
                    gpr.game_date,
                    gpr.season,
                    gpr.season_type,
                    gpr.game_status,
                    gpr.game_status_text,
                    gpr.home_team_score,
                    gpr.away_team_score,
                    gpr.home_win_probability_logistic,
                    gpr.home_win_probability_rf,
                    gpr.prediction_correct,
                    gpr.arena_name,
                    gpr.arena_city,
                    ht.team_name as home_team,
                    at.team_name as away_team
                FROM game_predictions_results gpr
                JOIN teams ht ON gpr.home_team_id = ht.team_id
                JOIN teams at ON gpr.away_team_id = at.team_id
                WHERE 1=1 {0}
                ORDER BY gpr.game_date {1}, gpr.id {1}
                LIMIT %s OFFSET %s
            '''.format(date_condition, 'ASC' if sort_order == 'asc' else 'DESC')
            
            all_params = query_params + [per_page, offset]
            cursor.execute(query, all_params)
            predictions_data = cursor.fetchall()

            # Format predictions
            predictions = []
            for pred in predictions_data:
                lr_home_prob = float(pred['home_win_probability_logistic'])
                rf_home_prob = float(pred['home_win_probability_rf'])
                
                lr_prediction = {
                    'winner': pred['home_team'] if lr_home_prob > 0.5 else pred['away_team'],
                    'probability': max(lr_home_prob, 1 - lr_home_prob) * 100
                }
                
                rf_prediction = {
                    'winner': pred['home_team'] if rf_home_prob > 0.5 else pred['away_team'],
                    'probability': max(rf_home_prob, 1 - rf_home_prob) * 100
                }

                prediction = {
                    'game_info': {
                        'date': pred['game_date'],
                        'season': pred['season'],
                        'season_type': pred['season_type']
                    },
                    'teams': {
                        'home_team': pred['home_team'],
                        'away_team': pred['away_team']
                    },
                    'score': {
                        'home_score': pred['home_team_score'],
                        'away_score': pred['away_team_score'],
                        'status': pred['game_status_text']
                    },
                    'venue': {
                        'arena': pred['arena_name'],
                        'city': pred['arena_city']
                    },
                    'model_predictions': {
                        'logistic_regression': {
                            'home_win_prob': lr_home_prob,
                            'away_win_prob': 1 - lr_home_prob,
                            'prediction': lr_prediction
                        },
                        'random_forest': {
                            'home_win_prob': rf_home_prob,
                            'away_win_prob': 1 - rf_home_prob,
                            'prediction': rf_prediction
                        }
                    },
                    'prediction_result': {
                        'status': pred['game_status_text'],
                        'correct': bool(pred['prediction_correct']) if pred['game_status'] == 3 else None
                    }
                }
                predictions.append(prediction)

            cursor.close()
            conn.close()

            return render_template('predict.html',
                                predictions=predictions,
                                page=page,
                                total_pages=total_pages,
                                total_records=total_records,
                                sort_order=sort_order,
                                date_filter=date_filter,
                                start_date=start_date)

        except Exception as e:
            cursor.close()
            conn.close()
            raise e

    except Exception as e:
        app.logger.error(f"Error in predict route: {str(e)}")
        app.logger.error(traceback.format_exc())
        return render_template('error.html', error="An error occurred while loading predictions")

@app.route('/models')
@login_required
def models():
    try:
        print(f"User {current_user.username} accessed models page")
        return render_template('models.html')
    except Exception as e:
        print(f"Error in models route: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 初始化数据库
init_db()

if __name__ == '__main__':
    app.run(debug=True) 