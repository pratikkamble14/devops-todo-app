import pytest
import sys
import os
import json

# Add app directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.app import app, USERS_FILE, TODOS_DIR


@pytest.fixture
def client():
    """
    Create a Flask test client with a clean test environment
    """
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Cleanup before tests
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)

    if os.path.exists(TODOS_DIR):
        for f in os.listdir(TODOS_DIR):
            os.remove(os.path.join(TODOS_DIR, f))

    with app.test_client() as client:
        yield client


@pytest.fixture
def registered_user(client):
    """
    Register a test user
    """
    return client.post(
        "/register",
        data={
            "username": "testuser",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )


@pytest.fixture
def logged_in_client(client, registered_user):
    """
    Login the test user
    """
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )
    return client


def test_home_page(logged_in_client):
    """
    Home page should load for authenticated user
    """
    response = logged_in_client.get("/")
    assert response.status_code == 200


def test_health_check(client):
    """
    Health endpoint should be publicly accessible
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert b"healthy" in response.data


def test_add_todo(logged_in_client):
    """
    Add todo should work for logged-in user
    """
    response = logged_in_client.post(
        "/add",
        data={"todo": "Test Todo"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Test Todo" in response.data
