from utils.db import get_session
from utils.models import User
from sqlmodel import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_user(email: str, password: str, full_name: str | None = None, role: str = "student"):
    with get_session() as session:
        q = select(User).where(User.email == email)
        existing = session.exec(q).first()
        if existing:
            raise ValueError("User already exists")
        user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def authenticate_user(email: str, password: str):
    with get_session() as session:
        q = select(User).where(User.email == email)
        user = session.exec(q).first()
        if not user:
            return None
        if verify_password(password, user.password_hash):
            return user
        return None


def get_user_by_id(user_id: int):
    with get_session() as session:
        return session.get(User, user_id)
