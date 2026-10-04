from typing import Literal
from pydantic import BaseModel, Field

Topic = Literal['select', 'where', 'null', 'distinct', 'order', 'inner', 'left']


class Exercise(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    topic: Topic
    prompt: str = Field(min_length=5, max_length=5000)
    reference_sql: str = Field(min_length=5, max_length=10000)
    hints: list[str] = Field(min_length=3, max_length=3)
    material_ids: list[str] = Field(default_factory=list)
    tables: list[str] = Field(min_length=1, max_length=2)
    order_matters: bool = False
    aliases_matter: bool = False


class SQLInput(BaseModel):
    sql: str = Field(min_length=1, max_length=10000)


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class Assignment(BaseModel):
    topic: Topic
    tables: list[str] = Field(min_length=1, max_length=2)


class Generation(BaseModel):
    material_ids: list[str] = Field(min_length=1)
    tables: list[str] = Field(min_length=1, max_length=2)
    count: int = Field(default=20, ge=1, le=20)


class SessionInput(BaseModel):
    topic: Topic | None = None
