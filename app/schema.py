# -------------------------
# Enum
# -------------------------
from enum import Enum
from typing import Annotated, Optional

# DeepSeek v4: added ConfigDict import for model_config
from pydantic import BaseModel, Field, ConfigDict


class Role(str, Enum):
    admin = "admin"
    user = "user"

# -------------------------
# Request Schema
# Used only for incoming data
# -------------------------
class UserCreate(BaseModel):
    first_name: Annotated[
        str,
        Field(...,description="First Name")
    ]

    last_name: Annotated[
        str,
        Field(...,description="Last Name")
    ]

    username: Annotated[
        str,
        Field(
            ...,
            min_length=5,
            max_length=50,
            description="Username",
        )
    ]

    email: Annotated[
        str,
        Field(
            ...,
            description="Email Address",
            examples=["john@gmail.com"],
        )
    ]

    password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            description="User Password",
        )
    ]

    role: Role

    phone: Annotated[
        str,
        Field(
            ...,
            description='User phone Number'
        )
    ]


class UpdateUser(BaseModel):
    last_name: Optional[str] = None
    # DeepSeek v4: fixed typo fast_name -> first_name (fast_name never
    # matched the User model field, so it was silently ignored)
    first_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

# DeepSeek v4: response schema for user profile - explicitly excludes
# hashed_password so it can't leak through GET /user
class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    role: Role
    is_active: bool
    phone: Optional[str] = None

    # DeepSeek v4: ConfigDict is the Pydantic v2 way (class Config is deprecated)
    model_config = ConfigDict(from_attributes=True)

class PasswordUpdate(BaseModel):
    current_password: str = Field(...)
    new_password: str = Field(...)


