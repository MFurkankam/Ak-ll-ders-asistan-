import random
import string
from utils.db import get_session
from utils.models import Class, Enrollment, Quiz, Question, Attempt
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete


def _generate_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def create_class(title: str, description: str, owner_id: int, code: str | None = None) -> Class:
    max_attempts = 8
    with get_session() as session:
        for _ in range(max_attempts):
            candidate = code or _generate_code()
            q = select(Class).where(Class.code == candidate)
            if session.exec(q).first():
                code = None
                continue
            cls = Class(
                title=title,
                description=description,
                owner_id=owner_id,
                code=candidate,
            )
            session.add(cls)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                code = None
                continue
            session.refresh(cls)
            # enroll owner as teacher in class
            enroll = Enrollment(class_id=cls.id, user_id=owner_id, role_in_class='teacher')
            session.add(enroll)
            session.commit()
            return cls
    raise ValueError("Unable to generate unique class code")


def join_class_by_code(code: str, user_id: int) -> Enrollment:
    with get_session() as session:
        q = select(Class).where(Class.code == code)
        cls = session.exec(q).first()
        if not cls:
            raise ValueError("Class not found")
        # check existing enrollment
        q2 = select(Enrollment).where(Enrollment.class_id == cls.id, Enrollment.user_id == user_id)
        existing = session.exec(q2).first()
        if existing:
            return existing
        enroll = Enrollment(class_id=cls.id, user_id=user_id, role_in_class='student')
        session.add(enroll)
        session.commit()
        session.refresh(enroll)
        return enroll


def get_user_classes(user_id: int):
    with get_session() as session:
        q = select(Class).join(Enrollment, Enrollment.class_id == Class.id).where(Enrollment.user_id == user_id)
        return list(session.exec(q))


def delete_class(class_id: int, user_id: int):
    with get_session() as session:
        cls = session.get(Class, class_id)
        if not cls:
            raise ValueError("Class not found")
        if cls.owner_id != user_id:
            raise PermissionError("Only class owner can delete the class")

        quizzes = list(session.exec(select(Quiz).where(Quiz.class_id == class_id)))
        quiz_ids = [q.id for q in quizzes]
        if quiz_ids:
            session.exec(delete(Question).where(Question.quiz_id.in_(quiz_ids)))
            session.exec(delete(Attempt).where(Attempt.quiz_id.in_(quiz_ids)))
            session.exec(delete(Quiz).where(Quiz.id.in_(quiz_ids)))

        session.exec(delete(Enrollment).where(Enrollment.class_id == class_id))
        session.exec(delete(Class).where(Class.id == class_id))
        session.commit()
        return True


def update_class(class_id: int, user_id: int, title: str, description: str | None = None) -> Class:
    with get_session() as session:
        cls = session.get(Class, class_id)
        if not cls:
            raise ValueError("Class not found")
        if cls.owner_id != user_id:
            raise PermissionError("Only class owner can update the class")

        cls.title = title
        cls.description = description
        session.add(cls)
        session.commit()
        session.refresh(cls)
        return cls
