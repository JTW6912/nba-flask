from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from sqlalchemy import text
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()  # 加载 .env 文件中的环境变量

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

# 配置数据库连接
MYSQL_USER = os.environ.get('MYSQLUSER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD')
MYSQL_HOST = os.environ.get('MYSQLHOST')
MYSQL_PORT = os.environ.get('MYSQLPORT', '3306')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE')

if all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE]):
    # 构建MySQL连接URL
    DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    
    # 配置 SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': int(os.environ.get('MAX_POOL_SIZE', '1')),
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 60,
            'use_pure': True
        }
    }
    logger.info("Database configuration completed")
else:
    logger.error("Missing required MySQL environment variables")
    raise ValueError("Required MySQL environment variables are missing")

# 初始化数据库
db = SQLAlchemy(app)

def get_db():
    try:
        result = db.session.execute(text('SELECT 1')).fetchone()
        logger.info(f"Database connection test successful: {result}")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Database URL format: {DATABASE_URL.split('@')[0]}@[HIDDEN]")
        logger.error(f"Engine options: {app.config['SQLALCHEMY_ENGINE_OPTIONS']}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# 数据库连接管理
@app.before_request
def before_request():
    try:
        if not get_db():
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        logger.error(f"Error in before_request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.teardown_request
def teardown_request(exception=None):
    if exception:
        logger.error(f"Exception in request: {str(exception)}")
        db.session.rollback()
    db.session.remove()

# 初始化数据库表
def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            logger.error(f"Database URL: {DATABASE_URL.split('@')[0]}@[HIDDEN]")

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
        logger.info("Accessing index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
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
            logger.info(f"New user registered: {user.username}")
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in registration: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password')
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
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
        # 示例数据 - 在实际应用中，这些数据应该从数据库获取
        recent_predictions = [
            {
                'date': '2024-03-15',
                'teams': 'Lakers vs Warriors',
                'prediction': 'Lakers Win',
                'result': 'Correct'
            },
            {
                'date': '2024-03-14',
                'teams': 'Celtics vs Bucks',
                'prediction': 'Celtics Win',
                'result': 'Incorrect'
            },
            {
                'date': '2024-03-13',
                'teams': 'Heat vs Nets',
                'prediction': 'Heat Win',
                'result': 'Correct'
            }
        ]
        
        logger.info(f"User {current_user.username} accessed dashboard")
        return render_template('dashboard.html', recent_predictions=recent_predictions)
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    try:
        username = current_user.username
        logout_user()
        logger.info(f"User {username} logged out")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    try:
        # 示例数据 - 在实际应用中，这些数据应该从数据库获取
        recent_predictions = [
            {
                'date': '2024-03-15',
                'teams': 'Lakers vs Warriors',
                'prediction': 'Lakers Win',
                'result': 'Correct'
            },
            {
                'date': '2024-03-14',
                'teams': 'Celtics vs Bucks',
                'prediction': 'Celtics Win',
                'result': 'Incorrect'
            },
            {
                'date': '2024-03-13',
                'teams': 'Heat vs Nets',
                'prediction': 'Heat Win',
                'result': 'Correct'
            }
        ]

        if request.method == 'POST':
            home_team = request.form.get('home_team')
            away_team = request.form.get('away_team')
            # 这里添加预测逻辑
            prediction = "Home Team Win"  # 示例预测结果
            win_probability = 75.5  # 示例概率
            confidence_score = 80.0  # 示例置信度
            
            logger.info(f"Prediction made for {home_team} vs {away_team}")
            return render_template('predict.html', 
                                prediction=prediction,
                                home_team=home_team,
                                away_team=away_team,
                                win_probability=win_probability,
                                confidence_score=confidence_score,
                                recent_predictions=recent_predictions)
        
        return render_template('predict.html', recent_predictions=recent_predictions)
    except Exception as e:
        logger.error(f"Error in predict route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/models')
@login_required
def models():
    try:
        logger.info(f"User {current_user.username} accessed models page")
        return render_template('models.html')
    except Exception as e:
        logger.error(f"Error in models route: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 初始化数据库
init_db() 