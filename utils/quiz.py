from typing import List, Dict, Any
from utils.db import get_session
from utils.models import Quiz, Question, Attempt
from sqlmodel import select
import json
from datetime import datetime, timezone
import unicodedata


def create_quiz(class_id: int, title: str, author_id: int, questions: List[Dict[str, Any]]):
    """questions: list of dicts: {type,text,choices(optional dict), correct_answer, topics(optional list), points}
    """
    with get_session() as session:
        quiz = Quiz(class_id=class_id, title=title, author_id=author_id)
        session.add(quiz)
        session.commit()
        session.refresh(quiz)

        for q in questions:
            choices = None
            if 'choices' in q and q['choices'] is not None:
                choices = json.dumps(q['choices'])
            topics = None
            if 'topics' in q and q['topics'] is not None:
                topics = json.dumps(q['topics'])
            question = Question(
                quiz_id=quiz.id,
                type=q.get('type'),
                text=q.get('text'),
                choices=choices,
                correct_answer=json.dumps(q.get('correct_answer')) if q.get('correct_answer') is not None else None,
                topics=topics,
                points=q.get('points', 1.0)
            )
            session.add(question)
        session.commit()

    return quiz


def get_quizzes_for_class(class_id: int):
    with get_session() as session:
        q = select(Quiz).where(Quiz.class_id == class_id)
        return list(session.exec(q))


def get_questions_for_quiz(quiz_id: int):
    with get_session() as session:
        q = select(Question).where(Question.quiz_id == quiz_id)
        return list(session.exec(q))


def publish_quiz(quiz_id: int, publish: bool = True):
    with get_session() as session:
        quiz = session.get(Quiz, quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")
        quiz.published = publish
        session.add(quiz)
        session.commit()
        session.refresh(quiz)
        return quiz


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def _normalize_text(t: str | None) -> str:
    if t is None:
        return ""
    text = _strip_accents(str(t)).lower().strip()
    return "".join(e for e in text if e.isalnum() or e.isspace())


def _normalize_true_false(value) -> str:
    if value is None:
        return ""
    text = _strip_accents(str(value)).strip().lower()
    if text in ("true", "t", "1", "yes", "y", "dogru"):
        return "true"
    if text in ("false", "f", "0", "no", "n", "yanlis"):
        return "false"
    return text


def grade_attempt(quiz_id: int, user_id: int, answers: List[Dict[str, Any]]):
    """answers: list of {question_id, answer}
    Returns dict with score and per_question results
    """
    questions = {q.id: q for q in get_questions_for_quiz(quiz_id)}
    total = 0.0
    score = 0.0
    per_q = []

    for ans in answers:
        qid = ans['question_id']
        provided = ans.get('answer')
        q = questions.get(qid)
        if not q:
            continue
        total += q.points or 1.0
        correct = False
        correct_val = None
        if q.correct_answer:
            try:
                correct_val = json.loads(q.correct_answer)
            except Exception:
                correct_val = q.correct_answer
        # MCQ or TF
        if q.type == 'mcq':
            if isinstance(correct_val, (list, dict)):
                # if stored as structure
                correct_choice = correct_val
            else:
                correct_choice = str(correct_val)
            if str(provided).strip().lower() == str(correct_choice).strip().lower():
                correct = True
        elif q.type == 'true_false':
            if _normalize_true_false(provided) == _normalize_true_false(correct_val):
                correct = True
        elif q.type == 'fill_blank':
            if isinstance(correct_val, str):
                if _normalize_text(provided) == _normalize_text(correct_val):
                    correct = True
        elif q.type == 'short_answer':
            # simple keyword match: correct_val can be list of keywords or sample
            if isinstance(correct_val, list):
                norm = _normalize_text(provided)
                matches = sum(1 for kw in correct_val if kw.lower() in norm)
                if matches / max(1, len(correct_val)) >= 0.5:
                    correct = True
            else:
                # fallback to substring
                if _normalize_text(str(correct_val)) in _normalize_text(str(provided)):
                    correct = True
        per_q.append({
            'question_id': qid,
            'correct': correct,
            'points': q.points or 1.0
        })
        if correct:
            score += q.points or 1.0

    # Save attempt
    with get_session() as session:
        attempt = Attempt(
                quiz_id=quiz_id,
                user_id=user_id,
                answers=json.dumps(answers),
                per_question=json.dumps(per_q),
                score=score,
                max_score=total,
                finished_at=datetime.now(timezone.utc)
            )
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

    return {'score': score, 'max_score': total, 'per_question': per_q, 'attempt_id': attempt.id}


def get_attempts_for_class(class_id: int, quiz_id: int = None, user_email: str = None, since: str = None, until: str = None):
    """Return attempts for a class with optional filters.
    since/until should be ISO date strings (YYYY-MM-DD) or None.
    """
    from utils.models import Attempt, Quiz, User
    with get_session() as session:
        q = select(Quiz).where(Quiz.class_id == class_id)
        quizzes = list(session.exec(q))
        quiz_map = {quiz.id: quiz for quiz in quizzes}
        quiz_ids = list(quiz_map.keys())
        if not quiz_ids:
            return []

        aquery = select(Attempt).where(Attempt.quiz_id.in_(quiz_ids))
        if quiz_id is not None:
            aquery = aquery.where(Attempt.quiz_id == quiz_id)
        if user_email:
            u = session.exec(select(User).where(User.email == user_email)).first()
            if u:
                aquery = aquery.where(Attempt.user_id == u.id)
            else:
                return []
        if since:
            try:
                from datetime import datetime
                since_dt = datetime.fromisoformat(since)
                aquery = aquery.where(Attempt.finished_at >= since_dt)
            except Exception:
                pass
        if until:
            try:
                from datetime import datetime
                until_dt = datetime.fromisoformat(until)
                aquery = aquery.where(Attempt.finished_at <= until_dt)
            except Exception:
                pass

        attempts = list(session.exec(aquery))
        results = []
        for at in attempts:
            user = session.get(User, at.user_id)
            results.append({
                'attempt_id': at.id,
                'quiz_id': at.quiz_id,
                'quiz_title': quiz_map.get(at.quiz_id).title if quiz_map.get(at.quiz_id) else '',
                'user_id': at.user_id,
                'user_email': user.email if user else '',
                'user_full_name': user.full_name if user else '',
                'score': at.score,
                'max_score': at.max_score,
                'per_question': json.loads(at.per_question) if at.per_question else None,
                'finished_at': at.finished_at.isoformat() if at.finished_at else None
            })
        return results


def get_attempt_detail(attempt_id: int):
    """Return rich attempt details including question texts and per-question correctness"""
    from utils.models import Attempt, Question, Quiz
    with get_session() as session:
        at = session.get(Attempt, attempt_id)
        if not at:
            return None
        quiz = session.get(Quiz, at.quiz_id)
        per_q = json.loads(at.per_question) if at.per_question else []
        detailed = []
        for pq in per_q:
            qobj = session.get(Question, pq.get('question_id'))
            detailed.append({
                'question_id': pq.get('question_id'),
                'question_text': qobj.text if qobj else '',
                'type': qobj.type if qobj else '',
                'correct': pq.get('correct'),
                'points': pq.get('points')
            })
        return {
            'attempt_id': at.id,
            'quiz_id': at.quiz_id,
            'quiz_title': quiz.title if quiz else '',
            'user_id': at.user_id,
            'answers': json.loads(at.answers) if at.answers else None,
            'per_question': detailed,
            'score': at.score,
            'max_score': at.max_score,
            'finished_at': at.finished_at.isoformat() if at.finished_at else None
        }


def compute_topic_mastery(class_id: int, attempts: list = None):
    """Returns dict: topic -> {'correct':int,'attempts':int,'mastery':float}
    If attempts list is provided, use it instead of querying all attempts for the class.
    """
    from utils.models import Quiz, Question, Attempt
    with get_session() as session:
        q = select(Quiz).where(Quiz.class_id == class_id)
        quizzes = list(session.exec(q))
        if not quizzes:
            return {}
        quiz_ids = [qq.id for qq in quizzes]
        qq = select(Question).where(Question.quiz_id.in_(quiz_ids))
        questions = list(session.exec(qq))
        q_map = {q.id: q for q in questions}

        if attempts is None:
            aquery = select(Attempt).where(Attempt.quiz_id.in_(quiz_ids))
            attempts_db = list(session.exec(aquery))
            attempts_list = []
            for at in attempts_db:
                attempts_list.append({
                    'per_question': json.loads(at.per_question) if at.per_question else None
                })
        else:
            attempts_list = attempts

        topic_stats: Dict[str, Dict[str, int]] = {}

        for at in attempts_list:
            per_q = at.get('per_question')
            if not per_q:
                continue
            for pq in per_q:
                qid = pq.get('question_id')
                correct = bool(pq.get('correct'))
                qobj = q_map.get(qid)
                if not qobj:
                    continue
                topics = []
                if qobj.topics:
                    try:
                        topics = json.loads(qobj.topics)
                    except Exception:
                        # fallback comma separated
                        topics = [t.strip() for t in (qobj.topics or '').split(',') if t.strip()]
                for t in topics:
                    if t not in topic_stats:
                        topic_stats[t] = {'correct':0,'attempts':0}
                    topic_stats[t]['attempts'] += 1
                    if correct:
                        topic_stats[t]['correct'] += 1

        # compute mastery
        result = {}
        for t,vals in topic_stats.items():
            attempts_count = vals['attempts']
            correct_count = vals['correct']
            mastery = (correct_count / attempts_count) if attempts_count > 0 else 0.0
            result[t] = {'correct': correct_count, 'attempts': attempts_count, 'mastery': mastery}
        return result


# compute_topic_mastery: single implementation is above (supports optional 'attempts' parameter)
# removed duplicate implementation to avoid override and confusion

