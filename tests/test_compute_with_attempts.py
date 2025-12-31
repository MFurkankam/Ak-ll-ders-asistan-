from utils.db import init_db, get_session
from utils.models import User, Class
from utils.quiz import create_quiz, grade_attempt, get_attempts_for_class, compute_topic_mastery, get_questions_for_quiz, get_quizzes_for_class


def test_compute_with_filtered_attempts():
    init_db()
    # setup
    with get_session() as s:
        teacher = User(email='tw@example.com', password_hash='x', full_name='T', role='teacher')
        s.add(teacher); s.commit(); s.refresh(teacher)
        teacher_id = teacher.id
        cl = Class(title='CWT', code='CWT1', description='x', owner_id=teacher_id)
        s.add(cl); s.commit(); s.refresh(cl)
        class_id = cl.id

    questions = [
        {'type':'mcq','text':'Q1','choices':{'A':'1','B':'2'},'correct_answer':'A','topics':['t1'],'points':1},
        {'type':'mcq','text':'Q2','choices':{'A':'x','B':'y'},'correct_answer':'B','topics':['t2'],'points':1}
    ]
    create_quiz(class_id, 'CWT Quiz', teacher_id, questions)

    quizzes = get_quizzes_for_class(class_id)
    quiz_obj = [q for q in quizzes if q.title == 'CWT Quiz'][0]
    qs = get_questions_for_quiz(quiz_obj.id)

    # student attempts
    with get_session() as s:
        s1 = User(email='s_cw1@example.com', password_hash='x', full_name='S1', role='student')
        s.add(s1); s.commit(); s.refresh(s1)
        s1id = s1.id
        s2 = User(email='s_cw2@example.com', password_hash='x', full_name='S2', role='student')
        s.add(s2); s.commit(); s.refresh(s2)
        s2id = s2.id

    # student1 answers both correct
    grade_attempt(quiz_obj.id, s1id, [{'question_id': qs[0].id, 'answer':'A'},{'question_id': qs[1].id, 'answer':'B'}])
    # student2 answers Q1 wrong, Q2 correct
    grade_attempt(quiz_obj.id, s2id, [{'question_id': qs[0].id, 'answer':'B'},{'question_id': qs[1].id, 'answer':'B'}])

    attempts = get_attempts_for_class(class_id)
    # now compute mastery only over filtered attempts (e.g., only student1)
    filtered = get_attempts_for_class(class_id, user_email='s_cw1@example.com')
    stats = compute_topic_mastery(class_id, attempts=filtered)
    assert stats['t1']['correct'] == 1 and stats['t1']['attempts'] == 1
    assert stats['t2']['correct'] == 1 and stats['t2']['attempts'] == 1
    print('compute_with_filtered_attempts passed')
