from enum import Enum
from typing import Annotated
from datetime import timedelta, datetime, timezone

from dns.asyncbackend import AsyncLibraryNotFoundError
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt

from app.dependencies import get_db
from app.models import User
from app.schema import UserCreate, UpdateUser, PasswordUpdate

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = '86246bdacd0b6b86cd83d28990e55d90cb4e18f8190da345d47a14c9e19e98b2'
ALGORITHM = 'HS256'



# Password hashing
bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/login')


def authenticate_user(username, password, db):
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        return False
    if bcrypt_context.verify(password,user.hashed_password):
        return user
    return False



def create_access_token(
        username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {
        'sub': username,
        'id': user_id,
        'role': role
    }
    expires = datetime.now(timezone.utc) + expires_delta
    # pyrefly: ignore [no-matching-overload]
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])

        # pyrefly: ignore [bad-assignment]
        username: str = payload.get('sub')
        # pyrefly: ignore [bad-assignment]
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        return {
            'username':username,
            'id': user_id,
            'role': role,
        }
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )


user_dependency = Annotated[dict, Depends(get_current_user)]


# -------------------------
# Create User
# -------------------------
@router.post(
    "/create-user",
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    new_user: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new user.
    """

    # Convert request data into SQLAlchemy model
    user = User(
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        email=new_user.email,

        # Never store plain-text passwords.
        hashed_password=bcrypt_context.hash(
            new_user.password
        ),

        role=new_user.role,
        is_active=True,
        phone= new_user.phone
    )

    # Save to database
    db.add(user)

    # Commit transaction
    db.commit()

    # Return created user
    # Later you'll replace this with a response model.
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'message' : 'User crated successfully'
        }
    )


@router.post('/login')
def login_user(
        db: Annotated[Session, Depends(get_db)],
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= 'Failed Authentication'
        )

    token = create_access_token(user.username,user.id, user.role, timedelta(minutes=30))

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.put('/edituser')
def update_todos(user: user_dependency, db: Annotated[Session, Depends(get_db)], update_user: UpdateUser):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    user = db.query(User).filter(User.id == user.get('id')).first()

    update_data = update_user.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(user,key,value)

    db.commit()
    return JSONResponse(
        status_code=200,
        content={
            'message' : 'User updated successfully'
        }
    )


@router.put('/editpassword')
def update_pass(
    user: user_dependency,
    db: Annotated[Session, Depends(get_db)],
    updatePassword: PasswordUpdate
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    user = db.query(User).filter(User.id == user.get('id')).first()

    if not bcrypt_context.verify(updatePassword.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Error on password change: current password incorrect'
        )

    user.hashed_password = bcrypt_context.hash(updatePassword.new_password)
    db.add(user)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': 'Password updated successfully'
        }
    )
