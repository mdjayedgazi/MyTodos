from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User, Todo
from router import auth

router = APIRouter(prefix="/admin", tags=["Admin"])  # DeepSeek v4: tag was "Authentication"

user_dependency = Annotated[dict, Depends(auth.get_current_user)]


@router.get('/todo')
def read_all(user: user_dependency, db: Annotated[Session, Depends(get_db)]):
    # DeepSeek v4: fixed the role check - the old code was
    # user.get('admin' != 'admin') which ALWAYS evaluated to False,
    # so any logged-in user could read all todos.
    if user is None or user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Failed Authentication'
        )

    return db.query(Todo).all()


@router.delete('/delete/{todo_id}')
def delete_todo(user: user_dependency, db: Annotated[Session, Depends(get_db)], todo_id: int):

    # DeepSeek v4: same role-check bug fixed here too (was 401, now 403)
    if user is None or user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Failed Authentication'
        )

    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='To do not found'
        )
    db.query(Todo).filter(Todo.id == todo_id).delete()

    db.commit()
    return JSONResponse(
        status_code=200,
        content={
            'message': 'To do deleted successfully'
        }
    )
