from utils.db import init_db, get_session
from utils.models import User, Class
from utils.quiz import create_quiz, grade_attempt, get_attempts_for_class, get_questions_for_quiz, get_quizzes_for_class


def test_attempt_filtering():
    init_db()
    # setup
    with get_session() as s:
        t = User(email='tf@example.com', password_hash='x', full_name='T', role='teacher')
        s.add(t)
        s.commit()
        s.refresh(t)
        teacher_id = t.id
        cl = Class(title='FilterClass', code='F1', description='x', owner_id=teacher_id)
        s.add(cl)
        s.commit()
        s.refresh(cl)
        class_id = cl.id
    
    questions = [
        {
            'type': 'mcq',
            'text': 'Q1',
            'choices': {'A': '1', 'B': '2'},
            'correct_answer': 'A',
            'topics': ['t1'],
            'points': 1,
        },
    ]
    create_quiz(class_id, 'Filter Quiz', teacher_id, questions)
    quizzes = get_quizzes_for_class(class_id)
    quiz_obj = [q for q in quizzes if q.title == 'Filter Quiz'][0]

    # student1 attempt
    with get_session() as s:
        s1 = User(email='sfilter1@example.com', password_hash='x', full_name='S1', role='student')
        s.add(s1); s.commit(); s.refresh(s1)
        s1id = s1.id
    qs = get_questions_for_quiz(quiz_obj.id)
    grade_attempt(quiz_obj.id, s1id, [{'question_id': qs[0].id, 'answer':'A'}])

    # student2 attempt
    with get_session() as s:
        s2 = User(email='sfilter2@example.com', password_hash='x', full_name='S2', role='student')
        s.add(s2); s.commit(); s.refresh(s2)
        s2id = s2.id
    grade_attempt(quiz_obj.id, s2id, [{'question_id': qs[0].id, 'answer':'B'}])

    # no filter -> 2 attempts
    all_attempts = get_attempts_for_class(class_id)
    assert len(all_attempts) == 2

    # filter by quiz_id
    q_attempts = get_attempts_for_class(class_id, quiz_id=quiz_obj.id)
    assert len(q_attempts) == 2

    # filter by student email
    s1_attempts = get_attempts_for_class(class_id, user_email='sfilter1@example.com')
    assert len(s1_attempts) == 1
    assert s1_attempts[0]['user_email'] == 'sfilter1@example.com'

    print('Filter tests passed')
