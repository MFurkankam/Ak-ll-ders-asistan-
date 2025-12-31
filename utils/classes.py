import random
import string
from utils.db import get_session
from utils.models import Class, Enrollment
from sqlmodel import select


def _generate_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def create_class(title: str, description: str, owner_id: int, code: str | None = None) -> Class:
    if code is None:
        code = _generate_code()
    with get_session() as session:
        # ensure unique code
        q = select(Class).where(Class.code == code)
        existing = session.exec(q).first()
        if existing:
            code = _generate_code()
        cls = Class(title=title, description=description, owner_id=owner_id, code=code)
        session.add(cls)
        session.commit()
        session.refresh(cls)
        # enroll owner as teacher in class
        enroll = Enrollment(class_id=cls.id, user_id=owner_id, role_in_class='teacher')
        session.add(enroll)
        session.commit()
        return cls


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
