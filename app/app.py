from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
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

# Generate a secure secret key
app.secret_key = secrets.token_hex(32)  # Generates a random 64-character hex string

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# File paths
USERS_FILE = 'users.json'
TODOS_DIR = 'todos'

# Ensure todos directory exists
os.makedirs(TODOS_DIR, exist_ok=True)


# User class
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


# User management functions
def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    users = load_users()
    if user_id in users:
        user_data = users[user_id]
        return User(user_id, user_data['username'], user_data['password_hash'])
    return None


# Todo management functions
def load_todos():
    """Load todos for current logged-in user"""
    if not current_user.is_authenticated:
        return []
    
    user_todo_file = os.path.join(TODOS_DIR, f'user_{current_user.id}.json')
    if os.path.exists(user_todo_file):
        with open(user_todo_file, 'r') as f:
            return json.load(f)
    return []


def save_todos(todos):
    """Save todos for current logged-in user"""
    if not current_user.is_authenticated:
        return
    
    user_todo_file = os.path.join(TODOS_DIR, f'user_{current_user.id}.json')
    with open(user_todo_file, 'w') as f:
        json.dump(todos, f, indent=2)


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='Please fill in all fields')
        
        users = load_users()
        
        # Find user by username
        user_id = None
        for uid, user_data in users.items():
            if user_data['username'] == username:
                user_id = uid
                break
        
        if user_id and check_password_hash(users[user_id]['password_hash'], password):
            user = User(user_id, username, users[user_id]['password_hash'])
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not password or not confirm_password:
            return render_template('register.html', error='Please fill in all fields')
        
        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        users = load_users()
        
        # Check if username already exists
        for user_data in users.values():
            if user_data['username'].lower() == username.lower():
                return render_template('register.html', error='Username already exists')
        
        # Create new user
        user_id = str(len(users) + 1)
        users[user_id] = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        
        logger.info(f"New user registered: {username}")
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))


# Todo routes
@app.route('/')
@login_required
def index():
    """Home page - displays all todos for logged-in user"""
    todos = load_todos()
    logger.info(f"User {current_user.username} loaded home page with {len(todos)} todos")
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
@login_required
def add_todo():
    """Add a new todo item"""
    todo_text = request.form.get('todo', '').strip()
    
    if todo_text:
        todos = load_todos()
        
        # Generate new ID
        new_id = max([todo['id'] for todo in todos], default=0) + 1
        
        new_todo = {
            'id': new_id,
            'text': todo_text,
            'completed': False,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        todos.append(new_todo)
        save_todos(todos)
        logger.info(f"User {current_user.username} added new todo: {todo_text}")
    
    return redirect(url_for('index'))


@app.route('/complete/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    """Mark a todo as completed"""
    todos = load_todos()
    
    for todo in todos:
        if todo['id'] == todo_id:
            todo['completed'] = True
            todo['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"User {current_user.username} completed todo ID: {todo_id}")
            break
    
    save_todos(todos)
    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    """Delete a todo item"""
    todos = load_todos()
    todos = [t for t in todos if t['id'] != todo_id]
    save_todos(todos)
    logger.info(f"User {current_user.username} deleted todo ID: {todo_id}")
    return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint - used by monitoring systems"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'authenticated_users': len(load_users())
    })


if __name__ == '__main__':
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)