from typing import Annotated
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# DeepSeek v4: removed unused imports (BaseModel, Field - schemas live in app/schema.py)
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt

from app.config import settings
from app.dependencies import get_db
from app.models import User
from app.schema import UserCreate, UpdateUser, PasswordUpdate

router = APIRouter(prefix="/auth", tags=["Authentication"])

# DeepSeek v4: SECRET_KEY/ALGORITHM moved to app/config.py (.env),
# old hardcoded key was already pushed to GitHub and is rotated.
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM



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
    # DeepSeek v4: bare `except:` caught every error (even our own
    # HTTPException) and returned 404. Now only jwt errors are caught
    # and the status is 401 Unauthorized, as it should be.
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found'
            )

        return {
            'username': username,
            'id': user_id,
            'role': role,
        }
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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

    # DeepSeek v4: check for duplicate username/email before insert,
    # otherwise the DB raises IntegrityError and the API returns 500.
    if db.query(User).filter(
        (User.username == new_user.username) | (User.email == new_user.email)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username or email already registered'
        )

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
            'message': 'User created successfully'  # DeepSeek v4: fixed typo "crated" -> "created"
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
def update_user(user: user_dependency, db: Annotated[Session, Depends(get_db)], update_user: UpdateUser):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    # DeepSeek v4: renamed update_todos -> update_user, and added a
    # None check so setattr() can't crash with AttributeError (500).
    user = db.query(User).filter(User.id == user.get('id')).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

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

    # DeepSeek v4: added None check - if the user row is missing,
    # user.hashed_password would crash with AttributeError (500).
    user = db.query(User).filter(User.id == user.get('id')).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

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
