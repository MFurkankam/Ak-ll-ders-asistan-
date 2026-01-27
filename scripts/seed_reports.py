import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from sqlmodel import select

from utils.db import get_session
from utils.models import Class, User, Enrollment, Quiz, Question, Attempt
from utils.quiz import create_quiz


SEED_USER_PREFIX = "seed_student"
SEED_QUIZ_PREFIX = "[SEED]"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _pick_topics(pool, count):
    return random.sample(pool, k=min(count, len(pool)))


def main():
    parser = argparse.ArgumentParser(description="Seed report data for a class.")
    parser.add_argument("--class-code", required=True, help="Class code to seed.")
    parser.add_argument("--students", type=int, default=12)
    parser.add_argument("--quizzes", type=int, default=3)
    parser.add_argument("--topics", type=int, default=5)
    parser.add_argument("--questions", type=int, default=6)
    args = parser.parse_args()

    random.seed(42)

    with get_session() as session:
        cls = session.exec(select(Class).where(Class.code == args.class_code)).first()
        if not cls:
            raise SystemExit(f"Class not found for code: {args.class_code}")

        existing_seed = session.exec(
            select(Quiz).where(Quiz.class_id == cls.id)
        ).all()
        if any(q.title.startswith(SEED_QUIZ_PREFIX) for q in existing_seed):
            raise SystemExit(
                "Seed quizzes already exist for this class. "
                "Run scripts/seed_reports_cleanup.py first."
            )

    topic_pool = [
        "Tasar\u0131m Kal\u0131plar\u0131",
        "Veri Yap\u0131lar\u0131",
        "Algoritmalar",
        "Nesne Y\u00f6nelimli Programlama",
        "Veri Tabanlar\u0131",
        "A\u011f Programlama",
        "Yaz\u0131l\u0131m Mimarisi",
    ]
    topics = topic_pool[: max(1, args.topics)]

    with get_session() as session:
        cls = session.exec(select(Class).where(Class.code == args.class_code)).first()
        if not cls:
            raise SystemExit(f"Class not found for code: {args.class_code}")

        users = []
        for i in range(args.students):
            email = f"{SEED_USER_PREFIX}+{cls.code.lower()}_{i+1}@example.com"
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                user = User(
                    email=email,
                    password_hash="seed",
                    full_name=f"Seed Ogrenci {i+1}",
                    role="student",
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            users.append(user)

            existing = session.exec(
                select(Enrollment).where(
                    Enrollment.class_id == cls.id,
                    Enrollment.user_id == user.id,
                )
            ).first()
            if not existing:
                enroll = Enrollment(
                    class_id=cls.id,
                    user_id=user.id,
                    role_in_class="student",
                )
                session.add(enroll)
                session.commit()

        quizzes = []
        for qi in range(args.quizzes):
            quiz_title = f"{SEED_QUIZ_PREFIX} Deneme Quiz {qi+1}"
            question_defs = []
            for qn in range(args.questions):
                topic_list = _pick_topics(topics, 1)
                if qn % 3 == 0:
                    question_defs.append(
                        {
                            "type": "true_false",
                            "text": f"Seed soru TF {qi+1}-{qn+1}",
                            "correct_answer": "Do\u011fru",
                            "topics": topic_list,
                            "points": 1.0,
                        }
                    )
                else:
                    question_defs.append(
                        {
                            "type": "mcq",
                            "text": f"Seed soru MCQ {qi+1}-{qn+1}",
                            "choices": {"A": "Secenek A", "B": "Secenek B", "C": "Secenek C", "D": "Secenek D"},
                            "correct_answer": "A",
                            "topics": topic_list,
                            "points": 1.0,
                        }
                    )

            quiz = create_quiz(cls.id, quiz_title, cls.owner_id, question_defs)
            quiz.published = True
            session.add(quiz)
            session.commit()
            session.refresh(quiz)
            quizzes.append(quiz)

        # Create attempts with segments: riskli/orta/iyi
        for idx, user in enumerate(users):
            if idx % 3 == 0:
                success_rate = 0.35
            elif idx % 3 == 1:
                success_rate = 0.6
            else:
                success_rate = 0.85

            for quiz in quizzes:
                questions = session.exec(
                    select(Question).where(Question.quiz_id == quiz.id)
                ).all()
                attempt_count = 2 if idx % 2 == 0 else 1

                for attempt_i in range(attempt_count):
                    per_question = []
                    answers = []
                    score = 0.0
                    max_score = 0.0
                    for q in questions:
                        correct = random.random() < success_rate
                        per_question.append(
                            {
                                "question_id": q.id,
                                "correct": correct,
                                "points": q.points or 1.0,
                            }
                        )
                        answers.append({"question_id": q.id, "answer": "A"})
                        max_score += q.points or 1.0
                        if correct:
                            score += q.points or 1.0

                    finished_at = _now_utc() - timedelta(days=random.randint(0, 20))
                    attempt = Attempt(
                        quiz_id=quiz.id,
                        user_id=user.id,
                        answers=json.dumps(answers),
                        per_question=json.dumps(per_question),
                        score=score,
                        max_score=max_score,
                        finished_at=finished_at,
                    )
                    session.add(attempt)
                session.commit()

    print(
        f"Seed complete for class {cls.title} ({cls.code}). "
        f"Students={args.students}, Quizzes={args.quizzes}, Topics={len(topics)}"
    )


if __name__ == "__main__":
    main()
