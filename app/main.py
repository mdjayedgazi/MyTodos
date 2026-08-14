from typing import Annotated, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.dependencies import get_db
from app.models import Todo,User
from app.schema import UserResponse
from router import auth, admin

app = FastAPI()

class Todos(BaseModel):
    title: Annotated[str, Field(..., max_length=50,min_length=5, description='Todos Title')]
    description: Annotated[str, Field(..., description='Todos Description', max_length=50,min_length=5)]
    priority: Annotated[int, Field(..., description='Todos Priority', gt=0, le=5, examples=[2])]
    completed: Annotated[bool, Field(default=False)]

# DeepSeek v4: rebuilt Todos_update - the old Optional[Annotated[..., Field(default=None)]]
# pattern caused a Pydantic v2 UnsupportedFieldAttributeWarning.
class Todos_update(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=50)
    priority: Optional[int] = Field(default=None, gt=0, le=5)
    completed: Optional[bool] = None

Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(admin.router)

user_dependency = Annotated[dict, Depends(auth.get_current_user)]

@app.get("/")
def read_todos(user: user_dependency, db: Annotated[Session, Depends(get_db)]):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()

@app.get('/todo/{todo_id}')
def read_specific_todos(user: user_dependency,db: Annotated[Session, Depends(get_db)], todo_id: int):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    specific_todos =  db.query(Todo).filter(Todo.owner_id == user.get('id')).filter(Todo.id == todo_id).first()

    if specific_todos is not None:
        return specific_todos
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='To do not found')

@app.post('/create')
def create_todos(user: user_dependency, db: Annotated[Session, Depends(get_db)], new_todos : Todos):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )
    todo_model = Todo(**new_todos.model_dump(), owner_id= user.get('id'))
    db.add(todo_model)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'message' : 'To do create successfully'
        }
    )


@app.put('/edit/{todos_id}')
def update_todos(user: user_dependency, db: Annotated[Session, Depends(get_db)], todos_id: int, update_todo: Todos_update):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    todo = db.query(Todo).filter(Todo.owner_id == user.get('id')).filter(Todo.id == todos_id).first()

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='To Do not found')

    update_data = update_todo.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(todo,key,value)

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message' : 'To do updated successfully'
        }
    )



@app.delete('/delete/{todo_id}')
def delete_todo(user:user_dependency, db: Annotated[Session, Depends(get_db)], todo_id: int):

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    todo = db.query(Todo).filter(Todo.owner_id == user.get('id')).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='To do not found'
        )
    db.query(Todo).filter(Todo.owner_id == user.get('id')).filter(Todo.id == todo_id).delete()

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message' : 'To do deleted successfully'
        }
    )


# DeepSeek v4: added response_model=UserResponse so hashed_password
# is never returned to the client.
@app.get('/user', response_model=UserResponse)
def get_user(user: user_dependency, db: Annotated[Session, Depends(get_db)]):

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Failed Authentication'
        )

    return db.query(User).filter(User.id == user.get('id')).first()

