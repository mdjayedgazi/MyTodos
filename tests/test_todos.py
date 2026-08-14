# =============================================================
# Modified by DeepSeek v4 (2026-08-14)
# - Removed redundant test_todo() (DB insert already covered by
#   create_test_todo() + the API tests)
# - Removed dead id==0 cleanup code in test_create_todo()
# - Fixed test_delete_todo: todo must exist before DELETE (was 404)
# - Added admin permission tests (200 / 403) and user profile tests
# =============================================================
import pytest

from app.database import SessionLocal
from app.models import Todo, User
from tests.test_main import client
from app.main import app
from fastapi import status
from router.auth import get_current_user

def override_get_current_user():
    return {
        'id': 1,
        'username': 'tester',
        # DeepSeek v4: added role so admin endpoints can be tested
        'role': 'admin'
    }

app.dependency_overrides[get_current_user] = override_get_current_user


def create_test_todo():
    db = SessionLocal()
    db.add(Todo(
        id=100,
        title='title',
        description='description',
        priority=3,
        completed=False,
        owner_id=1
    ))
    db.commit()
    db.close()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    db = SessionLocal()
    # Clean up existing to prevent duplicate key errors
    db.query(Todo).filter(Todo.owner_id == 1).delete()
    db.query(User).filter(User.id == 1).delete()
    db.commit()

    # Create the tests user
    test_user = User(
        id=1,
        first_name="Test",
        last_name="User",
        username="tester",
        email="testuser@example.com",
        hashed_password="hashed_password",
        role="user"
    )
    db.add(test_user)
    db.commit()

    yield

    # Teardown
    db.query(Todo).filter(Todo.owner_id == 1).delete()
    db.query(User).filter(User.id == 1).delete()
    db.commit()
    db.close()

def test_read_todos():
    response = client.get('/')
    assert response.status_code == status.HTTP_200_OK

def test_read_specific_todos():
    create_test_todo()

    response = client.get('/todo/100')
    assert response.status_code == status.HTTP_200_OK


def test_create_todo():
    # NOTE (DeepSeek v4): No need to clean up todo with id == 0 here:
    # the Todos schema has no 'id' field, so pydantic ignores 'id': 0,
    # and the DB auto-assigns ids from Identity(start=101), never 0.
    request_data = {
        'title': 'string',
        'description': 'string',
        'priority': 1,
        'completed': True
    }

    response = client.post('/create', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'message' : 'To do create successfully'}


def test_edit_todo():
    create_test_todo()

    request_data = {
        'title': 'hello'
    }

    response = client.put('/edit/100', json=request_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message' : 'To do updated successfully'}

def test_delete_todo():
    # DeepSeek v4: create_test_todo() is required - the autouse fixture
    # wipes all owner_id==1 todos before each test, so DELETE would 404.
    create_test_todo()
    response = client.delete('/delete/100')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message' : 'To do deleted successfully'}


# DeepSeek v4: admin permission tests (router/admin.py)
def test_admin_read_all_todos():
    create_test_todo()
    response = client.get('/admin/todo')
    assert response.status_code == status.HTTP_200_OK


def test_admin_delete_todo():
    create_test_todo()
    response = client.delete('/admin/delete/100')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message' : 'To do deleted successfully'}


def test_admin_forbidden_for_normal_user():
    # DeepSeek v4: temporarily override the auth dependency with a
    # non-admin role, then restore it, to test the 403 role check.
    app.dependency_overrides[get_current_user] = lambda: {
        'id': 1,
        'username': 'tester',
        'role': 'user'
    }
    try:
        response = client.get('/admin/todo')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides[get_current_user] = override_get_current_user


# DeepSeek v4: user profile tests (app/main.py GET /user, router/auth.py PUT /auth/edituser)
def test_user_profile_does_not_leak_password():
    response = client.get('/user')
    assert response.status_code == status.HTTP_200_OK
    assert 'hashed_password' not in response.json()


def test_edit_user_profile():
    response = client.put('/auth/edituser', json={'first_name': 'Deep'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message' : 'User updated successfully'}

    profile = client.get('/user').json()
    assert profile['first_name'] == 'Deep'