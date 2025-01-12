from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()  # 加载 .env 文件中的环境变量

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# Supabase PostgreSQL 连接配置
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:060912Wjt@db.kbbpkicqzobcrbhhcrzz.supabase.co:5432/postgres")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 1,  # 最小连接数
    'max_overflow': 0,  # 最大连接数
    'pool_timeout': 30,  # 连接超时时间
    'pool_recycle': 1800,  # 连接回收时间
    'pool_pre_ping': True,  # 自动检测断开的连接
    'connect_args': {
        'connect_timeout': 10,  # 连接超时时间
        'keepalives': 1,  # 保持连接
        'keepalives_idle': 30,  # 空闲连接保持时间
        'keepalives_interval': 10,  # 连接保持间隔
        'keepalives_count': 5  # 连接保持次数
    }
}

try:
    db = SQLAlchemy(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    raise

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

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    db.session.rollback()
    return jsonify({"error": "Internal server error", "details": str(error)}), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

# Routes
@app.route('/')
def index():
    try:
        logger.info("Accessing index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

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

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    app.run(debug=True) 