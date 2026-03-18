from sqlmodel import SQLModel, Field

from app.models.enums import Role


class User(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password: str
    role: Role