from enum import Enum
from typing import Annotated
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt

from app.dependencies import get_db
from app.models import User, Todo
from router import auth

router = APIRouter(prefix="/admin", tags=["Authentication"])

user_dependency = Annotated[dict, Depends(auth.get_current_user)]


@router.get('/todo')
def read_all (user: user_dependency, db: Annotated[Session, Depends(get_db)]):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Failed Authentication'
        )

    return db.query(Todo).all()


@router.delete('/delete/{todo_id}')
def delete_todo(user:user_dependency, db: Annotated[Session, Depends(get_db)], todo_id: int):

    if user is None or user.get('admin' != 'admin'):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
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
            'message' : 'To do deleted successfully'
        }
    )