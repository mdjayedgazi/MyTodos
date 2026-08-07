# -------------------------
# Enum
# -------------------------
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field


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
        Field(description="First Name")
    ]

    last_name: Annotated[
        str,
        Field(description="Last Name")
    ]

    username: Annotated[
        str,
        Field(
            min_length=5,
            max_length=50,
            description="Username",
        )
    ]

    email: Annotated[
        str,
        Field(
            description="Email Address",
            examples=["john@gmail.com"],
        )
    ]

    password: Annotated[
        str,
        Field(
            min_length=8,
            description="User Password",
        )
    ]

    role: Role

    phone: Annotated[
        str,
        Field(
            description='User phone Number'
        )
    ]


class UpdateUser(BaseModel):
    fast_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)

class PasswordUpdate(BaseModel):
    current_password: str = Field(...)
    new_password: str = Field(...)


