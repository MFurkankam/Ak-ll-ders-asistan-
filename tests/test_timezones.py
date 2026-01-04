from datetime import timezone
from utils.db import init_db, get_session
from utils.models import User, Class, Quiz, Attempt


def test_datetime_fields_are_timezone_aware():
    init_db()
    with get_session() as s:
        teacher = User(email='tz_teacher@example.com', password_hash='x', full_name='T', role='teacher')
        s.add(teacher)
        s.flush()  # ensure defaults applied but before DB roundtrip
        # in-memory default should be timezone-aware
        assert teacher.created_at.tzinfo is not None and teacher.created_at.tzinfo == timezone.utc
        s.commit()

        cl = Class(
            title='TZClass', code='TZ1', description='x', owner_id=teacher.id
        )
        s.add(cl)
        s.flush()
        assert (
            cl.created_at.tzinfo is not None and cl.created_at.tzinfo == timezone.utc
        )
        s.commit()

        quiz = Quiz(class_id=cl.id, title='TZ Quiz', author_id=teacher.id)
        s.add(quiz)
        s.flush()
        assert (
            quiz.created_at.tzinfo is not None and quiz.created_at.tzinfo == timezone.utc
        )
        s.commit()

        student = User(email='tz_student@example.com', password_hash='x', full_name='S', role='student')
        s.add(student)
        s.flush()
        assert (
            student.created_at.tzinfo is not None and student.created_at.tzinfo == timezone.utc
        )
        s.commit()

        attempt = Attempt(quiz_id=quiz.id, user_id=student.id)
        s.add(attempt)
        s.flush()
        assert (
            attempt.started_at is not None and attempt.started_at.tzinfo is not None
            and attempt.started_at.tzinfo == timezone.utc
        )
        s.commit()
