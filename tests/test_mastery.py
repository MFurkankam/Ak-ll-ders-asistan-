from utils.db import init_db, get_session
from utils.models import User, Class
from utils.quiz import create_quiz, grade_attempt, compute_topic_mastery, get_quizzes_for_class, get_questions_for_quiz


def test_compute_topic_mastery():
    init_db()
    # setup teacher and class
    with get_session() as s:
        teacher = User(email='t_mastery@example.com', password_hash='x', full_name='T', role='teacher')
        s.add(teacher)
        s.commit()
        s.refresh(teacher)
        cl = Class(
            title='MasteryClass', code='M1', description='x', owner_id=teacher.id
        )
        s.add(cl)
        s.commit()
        s.refresh(cl)
        class_id = cl.id
        teacher_id = teacher.id

    questions = [
        {
            'type': 'mcq',
            'text': 'Q1',
            'choices': {'A': '1', 'B': '2', 'C': '3', 'D': '4'},
            'correct_answer': 'A',
            'topics': ['t1'],
            'points': 1,
        },
        {
            'type': 'mcq',
            'text': 'Q2',
            'choices': {'A': 'x', 'B': 'y', 'C': 'z', 'D': 'w'},
            'correct_answer': 'C',
            'topics': ['t1', 't2'],
            'points': 1,
        },
    ]
    create_quiz(class_id, 'Mastery Quiz', teacher_id, questions)

    # student1: answers both correct
    with get_session() as s:
        s1 = User(email='s1@example.com', password_hash='x', full_name='S1', role='student')
        s.add(s1); s.commit(); s.refresh(s1)
        s1id = s1.id

    # find persisted quiz and load its questions
    quizzes = get_quizzes_for_class(class_id)
    quiz_obj = [x for x in quizzes if x.title == 'Mastery Quiz'][0]
    qs = get_questions_for_quiz(quiz_obj.id)
    answers1 = [
        {
            'question_id': q.id,
            'answer': ("A" if q.text == 'Q1' else "C"),
        }
        for q in qs
    ]
    grade_attempt(quiz_obj.id, s1id, answers1)

    # student2: answers both incorrect
    with get_session() as s:
        s2 = User(email='s2@example.com', password_hash='x', full_name='S2', role='student')
        s.add(s2); s.commit(); s.refresh(s2)
        s2id = s2.id

    answers2 = [{'question_id': q.id, 'answer': 'Z'} for q in qs]
    grade_attempt(quiz_obj.id, s2id, answers2)

    stats = compute_topic_mastery(class_id)
    # For t1: both questions belong -> attempts=4 (2 students * 2 questions), correct=2 (student1 correct both)
    assert 't1' in stats
    assert stats['t1']['attempts'] == 4
    assert stats['t1']['correct'] == 2
    assert abs(stats['t1']['mastery'] - 0.5) < 1e-6

    # For t2: only Q2 -> attempts=2, correct=1
    assert 't2' in stats
    assert stats['t2']['attempts'] == 2
    assert stats['t2']['correct'] == 1
    assert abs(stats['t2']['mastery'] - 0.5) < 1e-6

    print('Mastery test passed')
