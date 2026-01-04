from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime as SA_DateTime
from pydantic import field_validator
from sqlalchemy.orm import reconstructor

def now_utc():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    password_hash: str
    full_name: Optional[str] = None
    role: str = Field(default="student")  # admin|teacher|student
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            SA_DateTime(timezone=True),
            default=now_utc,
        ),
    )

    @field_validator('created_at', mode='before')
    def _ensure_created_at_tz(cls, v):
        if v is None:
            return now_utc()
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @reconstructor
    def _reconcilation_set_created_at(self):
        if getattr(self, 'created_at', None) is not None and self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

class Class(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    code: str = Field(index=True, unique=True)
    description: Optional[str] = None
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            SA_DateTime(timezone=True),
            default=now_utc,
        ),
    )

    @field_validator('created_at', mode='before')
    def _ensure_created_at_tz(cls, v):
        if v is None:
            return now_utc()
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @reconstructor
    def _reconcilation_set_created_at(self):
        if getattr(self, 'created_at', None) is not None and self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

class Enrollment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="class.id")
    user_id: int = Field(foreign_key="user.id")
    role_in_class: str = Field(default="student")
    joined_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            SA_DateTime(timezone=True),
            default=now_utc,
        ),
    )

    @field_validator('joined_at', mode='before')
    def _ensure_joined_at_tz(cls, v):
        if v is None:
            return now_utc()
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @reconstructor
    def _reconcilation_set_joined_at(self):
        if getattr(self, 'joined_at', None) is not None and self.joined_at.tzinfo is None:
            self.joined_at = self.joined_at.replace(tzinfo=timezone.utc)

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="class.id")
    title: str
    author_id: int = Field(foreign_key="user.id")
    published: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            SA_DateTime(timezone=True),
            default=now_utc,
        ),
    )

    @field_validator('created_at', mode='before')
    def _ensure_created_at_tz(cls, v):
        if v is None:
            return now_utc()
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @reconstructor
    def _reconcilation_set_created_at(self):
        if getattr(self, 'created_at', None) is not None and self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quiz.id")
    type: str
    text: str
    choices: Optional[str] = None  # JSON
    correct_answer: Optional[str] = None
    topics: Optional[str] = None  # CSV or JSON list
    points: Optional[float] = Field(default=1.0)

class Attempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key="quiz.id")
    user_id: int = Field(foreign_key="user.id")
    answers: Optional[str] = None  # JSON
    per_question: Optional[str] = None  # JSON: list of {question_id, correct, points}
    score: Optional[float] = None
    max_score: Optional[float] = None
    started_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            SA_DateTime(timezone=True),
            default=now_utc,
        ),
    )
    finished_at: Optional[datetime] = None

    @field_validator('started_at', mode='before')
    def _ensure_started_at_tz(cls, v):
        if v is None:
            return now_utc()
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @reconstructor
    def _reconcilation_set_started_at(self):
        if getattr(self, 'started_at', None) is not None and self.started_at.tzinfo is None:
            self.started_at = self.started_at.replace(tzinfo=timezone.utc)
