from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Supabase PostgreSQL 连接配置
DATABASE_URL = "postgresql://postgres:060912Wjt@db.kbbpkicqzobcrbhhcrzz.supabase.co:5432/postgres"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/models')
@login_required
def models():
    # Read model evaluation metrics from model_comparison.txt
    metrics = {
        'logistic': {'accuracy': 'N/A', 'precision': 'N/A', 'recall': 'N/A', 'f1': 'N/A'},
        'rf': {'accuracy': 'N/A', 'precision': 'N/A', 'recall': 'N/A', 'f1': 'N/A'},
        'elo': {'accuracy': 'N/A', 'precision': 'N/A', 'recall': 'N/A', 'f1': 'N/A'}
    }
    
    try:
        with open(os.path.join(basedir, '../model_comparison/model_comparison.txt'), 'r') as f:
            lines = f.readlines()
            for line in lines[3:]:  # Skip header lines
                if line.strip():  # Skip empty lines
                    parts = line.strip().split()
                    if 'Logistic' in line:
                        metrics['logistic'] = {
                            'accuracy': f"{float(parts[-4]):.1%}",
                            'precision': f"{float(parts[-3]):.1%}",
                            'recall': f"{float(parts[-2]):.1%}",
                            'f1': f"{float(parts[-1]):.1%}"
                        }
                    elif 'Random' in line:
                        metrics['rf'] = {
                            'accuracy': f"{float(parts[-4]):.1%}",
                            'precision': f"{float(parts[-3]):.1%}",
                            'recall': f"{float(parts[-2]):.1%}",
                            'f1': f"{float(parts[-1]):.1%}"
                        }
                    elif 'ELO' in line:
                        metrics['elo'] = {
                            'accuracy': f"{float(parts[-4]):.1%}",
                            'precision': f"{float(parts[-3]):.1%}",
                            'recall': f"{float(parts[-2]):.1%}",
                            'f1': f"{float(parts[-1]):.1%}"
                        }
    except Exception as e:
        print(f"Error reading model comparison file: {str(e)}")
    
    return render_template('models.html',
                         logistic_metrics=metrics.get('logistic'),
                         rf_metrics=metrics.get('rf'),
                         elo_metrics=metrics.get('elo'))

@app.route('/predict')
@login_required
def predict():
    return render_template('predict.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 