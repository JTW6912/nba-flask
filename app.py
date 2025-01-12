from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(username=username).first():
                logger.warning(f"Registration attempt with existing username: {username}")
                flash('Username already exists')
                return redirect(url_for('register'))
                
            if User.query.filter_by(email=email).first():
                logger.warning(f"Registration attempt with existing email: {email}")
                flash('Email already registered')
                return redirect(url_for('register'))
                
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            flash('Registration successful')
            return redirect(url_for('login'))
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error in register route: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        logger.info(f"User {current_user.username} accessed dashboard")
        return render_template('dashboard.html')
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

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    app.run(debug=True) 