import pytest
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test home page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_health_check(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'healthy' in response.data

def test_add_todo(client):
    """Test adding a todo"""
    response = client.post('/add', data={'todo': 'Test Todo'}, follow_redirects=True)
    assert response.status_code == 200