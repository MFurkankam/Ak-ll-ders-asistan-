import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from sqlmodel import select

from utils.db import get_session
from utils.models import Class, User, Enrollment, Quiz, Question, Attempt


SEED_USER_PREFIX = "seed_student"
SEED_QUIZ_PREFIX = "[SEED]"


def main():
    parser = argparse.ArgumentParser(description="Cleanup seeded report data for a class.")
    parser.add_argument("--class-code", required=True, help="Class code to cleanup.")
    args = parser.parse_args()

    with get_session() as session:
        cls = session.exec(select(Class).where(Class.code == args.class_code)).first()
        if not cls:
            raise SystemExit(f"Class not found for code: {args.class_code}")

        quizzes = session.exec(select(Quiz).where(Quiz.class_id == cls.id)).all()
        seed_quizzes = [q for q in quizzes if q.title.startswith(SEED_QUIZ_PREFIX)]
        seed_quiz_ids = [q.id for q in seed_quizzes]

        if seed_quiz_ids:
            session.exec(select(Attempt))
            for qid in seed_quiz_ids:
                session.exec(
                    Attempt.__table__.delete().where(Attempt.quiz_id == qid)
                )
                session.exec(
                    Question.__table__.delete().where(Question.quiz_id == qid)
                )
                session.exec(
                    Quiz.__table__.delete().where(Quiz.id == qid)
                )

        seed_users = session.exec(
            select(User).where(User.email.like(f"{SEED_USER_PREFIX}+%"))
        ).all()
        seed_user_ids = [u.id for u in seed_users]

        if seed_user_ids:
            session.exec(
                Enrollment.__table__.delete().where(
                    Enrollment.class_id == cls.id,
                    Enrollment.user_id.in_(seed_user_ids),
                )
            )
            session.exec(
                Attempt.__table__.delete().where(Attempt.user_id.in_(seed_user_ids))
            )
            for uid in seed_user_ids:
                session.exec(
                    User.__table__.delete().where(User.id == uid)
                )

        session.commit()

    print(f"Seed cleanup complete for class code {args.class_code}.")


if __name__ == "__main__":
    main()
