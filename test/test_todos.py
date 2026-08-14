import pytest

from app.database import SessionLocal
from app.models import Todo, User
from test.test_main import client
from app.main import app
from fastapi import status
from router.auth import get_current_user

def override_get_current_user():
    return {
        'id': 1,
        'username': 'tester'
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

    # Create the test user
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

def test_todo():
    create_test_todo()

    # Verify it was inserted
    db = SessionLocal()
    inserted_todo = db.query(Todo).filter(Todo.id == 100).first()
    assert inserted_todo is not None
    assert inserted_todo.title == 'title'
    db.close()

def test_read_todos():
    response = client.get('/')
    assert response.status_code == status.HTTP_200_OK

def test_read_specific_todos():
    create_test_todo()

    response = client.get('/todo/100')
    assert response.status_code == status.HTTP_200_OK


def test_create_todo():
    # NOTE: No need to clean up todo with id == 0 here:
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
    create_test_todo()
    response = client.delete('/delete/100')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message' : 'To do deleted successfully'}