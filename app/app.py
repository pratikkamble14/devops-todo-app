from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import os
import logging

# Configure logging (records what happens in the app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# File to store todos (in production, we'd use a database)
TODO_FILE = 'todos.json'

def load_todos():
    """Load todos from JSON file"""
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    return []

def save_todos(todos):
    """Save todos to JSON file"""
    with open(TODO_FILE, 'w') as f:
        json.dump(todos, f, indent=2)

@app.route('/')
def index():
    """Home page - displays all todos"""
    todos = load_todos()
    logger.info(f"Loading home page with {len(todos)} todos")
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add_todo():
    """Add a new todo item"""
    todo_text = request.form.get('todo')
    if todo_text:
        todos = load_todos()
        new_todo = {
            'id': len(todos) + 1,
            'text': todo_text,
            'completed': False,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        todos.append(new_todo)
        save_todos(todos)
        logger.info(f"Added new todo: {todo_text}")
    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>')
def complete_todo(todo_id):
    """Mark a todo as completed"""
    todos = load_todos()
    for todo in todos:
        if todo['id'] == todo_id:
            todo['completed'] = True
            logger.info(f"Completed todo ID: {todo_id}")
            break
    save_todos(todos)
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete_todo(todo_id):
    """Delete a todo item"""
    todos = load_todos()
    todos = [t for t in todos if t['id'] != todo_id]
    save_todos(todos)
    logger.info(f"Deleted todo ID: {todo_id}")
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check endpoint - used by monitoring systems"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Run the Flask development server
    # host='0.0.0.0' means accessible from any IP
    # port=5000 is the default Flask port
    # debug=True gives detailed error messages
    app.run(host='0.0.0.0', port=5000, debug=True)