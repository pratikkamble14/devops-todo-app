from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import logging
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configs
app.secret_key = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ─── Models ───────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    todos         = db.relationship('Todo', backref='user', lazy=True, cascade='all, delete-orphan')


class Todo(db.Model):
    __tablename__ = 'todos'
    id           = db.Column(db.Integer, primary_key=True)
    text         = db.Column(db.String(500), nullable=False)
    completed    = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# Create tables
with app.app_context():
    db.create_all()


# ─── Auth ─────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error='Please fill in all fields')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password or not confirm_password:
            return render_template('register.html', error='Please fill in all fields')

        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')

        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')

        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registered: {username}")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))


# ─── Todo Routes ──────────────────────────────────────────

@app.route('/')
@login_required
def index():
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    logger.info(f"User {current_user.username} loaded {len(todos)} todos")
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
@login_required
def add_todo():
    todo_text = request.form.get('todo', '').strip()

    if todo_text:
        todo = Todo(text=todo_text, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
        logger.info(f"User {current_user.username} added todo: {todo_text}")

    return redirect(url_for('index'))


@app.route('/complete/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if todo:
        todo.completed    = True
        todo.completed_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"User {current_user.username} completed todo ID: {todo_id}")

    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if todo:
        db.session.delete(todo)
        db.session.commit()
        logger.info(f"User {current_user.username} deleted todo ID: {todo_id}")

    return redirect(url_for('index'))


# ─── Health Check ─────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '3.0.0',
        'total_users': User.query.count(),
        'total_todos': Todo.query.count()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
