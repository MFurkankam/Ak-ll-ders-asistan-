from sqlmodel import select

from utils.db import get_session
from utils.models import Summary


def create_summary(user_id: int, title: str, content: str) -> Summary:
    with get_session() as session:
        summary = Summary(user_id=user_id, title=title, content=content)
        session.add(summary)
        session.commit()
        session.refresh(summary)
        return summary


def get_summaries_for_user(user_id: int):
    with get_session() as session:
        q = select(Summary).where(Summary.user_id == user_id).order_by(Summary.created_at.desc())
        return list(session.exec(q))


def delete_summary(summary_id: int, user_id: int) -> bool:
    with get_session() as session:
        summary = session.get(Summary, summary_id)
        if not summary:
            raise ValueError("Summary not found")
        if summary.user_id != user_id:
            raise PermissionError("Summary owner mismatch")
        session.delete(summary)
        session.commit()
        return True
