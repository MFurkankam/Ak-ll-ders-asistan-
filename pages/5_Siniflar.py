import json
import io
import csv
from datetime import datetime

import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.classes import join_class_by_code, get_user_classes, delete_class
from utils.quiz import (
    get_quizzes_for_class,
    create_quiz,
    publish_quiz,
    get_questions_for_quiz,
    grade_attempt,
    compute_topic_mastery,
    get_attempts_for_class,
    get_attempt_detail,
)

st.set_page_config(page_title="Sınıflar", page_icon="🏫", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name, show_sources=False)


def format_compact_time(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            return str(value)
    if dt.tzinfo:
        dt = dt.astimezone()
    month_names = [
        "Ocak",
        "Şubat",
        "Mart",
        "Nisan",
        "Mayıs",
        "Haziran",
        "Temmuz",
        "Ağustos",
        "Eylül",
        "Ekim",
        "Kasım",
        "Aralık",
    ]
    month_name = month_names[dt.month - 1]
    return f"{dt.day} {month_name} {dt.strftime('%H:%M')}"


def format_score(score, max_score):
    def as_int_or_float(value):
        try:
            num = float(value)
        except (TypeError, ValueError):
            return value
        if num.is_integer():
            return int(num)
        return num

    return f"{as_int_or_float(score)}/{as_int_or_float(max_score)}"


def select_class_by_id(classes, class_id):
    for cls in classes:
        if cls.id == class_id:
            return cls
    return None


if st.session_state.user is None:
    st.info("Lütfen önce giriş yap.")
    st.stop()

user_role = st.session_state.user.get("role", "student")
classes = get_user_classes(st.session_state.user["id"])

selected_class_id = st.session_state.get("selected_class_id")
show_class_detail = st.session_state.get("show_class_detail", False)

if show_class_detail and selected_class_id:
    active_class = select_class_by_id(classes, selected_class_id)
    if active_class is None:
        st.session_state.show_class_detail = False
        st.session_state.selected_class_id = None
        st.rerun()

    st.session_state.last_class_id = active_class.id

    if st.button("< Sınıflar", type="secondary"):
        st.session_state.show_class_detail = False
        st.session_state.selected_class_id = None
        st.rerun()

    st.markdown(
        f"""
        <div class="hero">
            <h2>{active_class.title}</h2>
            <p>{active_class.description or ""}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if user_role == "student":
        st.subheader("Yayınlanan Quizler")
        quizzes = get_quizzes_for_class(active_class.id)
        pub_quizzes = [q for q in quizzes if q.published]
        if pub_quizzes:
            for pq in pub_quizzes:
                with st.expander(f"{pq.title} - Yayınlandı"):
                    st.write(
                        "Oluşturan: "
                        f"{pq.author_id} - Oluşturuldu: {format_compact_time(pq.created_at)}"
                    )
                    if st.button("Quiz'e Katıl", key=f"att_{pq.id}"):
                        qs = get_questions_for_quiz(pq.id)
                        st.session_state.current_attempt = {
                            "quiz_id": pq.id,
                            "questions": [
                                {
                                    "id": q.id,
                                    "type": q.type,
                                    "text": q.text,
                                    "choices": json.loads(q.choices) if q.choices else None,
                                }
                                for q in qs
                            ],
                        }
                        st.rerun()
        else:
            st.info("Henüz yayınlanmış bir quiz yok.")

        st.markdown("---")
        st.subheader("Denemelerim")
        attempts = get_attempts_for_class(
            active_class.id, user_email=st.session_state.user.get("email")
        )
        if attempts:
            for a in attempts:
                with st.expander(
                    f"{format_compact_time(a['finished_at'])} | {a['quiz_title']} | "
                    f"{format_score(a['score'], a['max_score'])}"
                ):
                    st.write(f"Attempt ID: {a['attempt_id']}")
                    det = get_attempt_detail(a["attempt_id"])
                    if det:
                        for pq in det["per_question"]:
                            st.write(
                                f"- ({'Doğru' if pq['correct'] else 'Yanlış'}) "
                                f"{pq['question_text']} [{pq['points']}]"
                            )
        else:
            st.info("Henüz deneme yok.")

    else:
        quizzes = get_quizzes_for_class(active_class.id)
        tab_quiz, tab_students, tab_attempts, tab_reports = st.tabs(
            ["Quiz Yönetimi", "Öğrenciler", "Denemeler", "Raporlar"]
        )

        with tab_quiz:
            st.subheader("Quiz Yönetimi")
            if quizzes:
                for q in quizzes:
                    with st.expander(f"{q.title} - {'Yayınlandı' if q.published else 'Taslak'}"):
                        st.write(
                            "Oluşturan: "
                            f"{q.author_id} - Oluşturuldu: {format_compact_time(q.created_at)}"
                        )
                        col_a, col_b = st.columns([1, 1])
                        with col_a:
                            if st.button(
                                "Yayınla" if not q.published else "Yayını Kapat",
                                key=f"pub_{q.id}",
                            ):
                                try:
                                    publish_quiz(q.id, publish=not q.published)
                                    st.success("Durum güncellendi")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Hata: {e}")
                        with col_b:
                            if st.button("Soruları Görüntüle", key=f"view_{q.id}"):
                                questions = get_questions_for_quiz(q.id)
                                for qq in questions:
                                    st.write(f"- ({qq.type}) {qq.text} [{qq.points} puan]")
            else:
                st.info("Henüz bu sınıfa ait quiz yok.")

        with tab_students:
            st.subheader("Öğrenci Listesi")
            attempts_all = get_attempts_for_class(active_class.id)
            if attempts_all:
                stats = {}
                for a in attempts_all:
                    email = a.get("user_email") or ""
                    full_name = a.get("user_full_name") or ""
                    score = a.get("score") or 0.0
                    max_score = a.get("max_score") or 0.0
                    if email not in stats:
                        stats[email] = {"score": 0.0, "max_score": 0.0, "name": full_name}
                    stats[email]["score"] += score
                    stats[email]["max_score"] += max_score

                rows = []
                for email, vals in stats.items():
                    total = vals["max_score"]
                    success = (vals["score"] / total * 100) if total > 0 else 0.0
                    display_name = vals["name"] or email
                    rows.append({"Öğrenci": display_name, "Başarı %": round(success, 1)})

                rows = sorted(rows, key=lambda r: r["Başarı %"], reverse=True)
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("Henüz öğrenci denemesi yok.")

        with tab_attempts:
            st.subheader("Denemeler")
            quiz_opts = ["Tüm quizler"] + [q.title for q in quizzes]
            sel_quiz_title = st.selectbox(
                "Quiz", quiz_opts, index=0, key=f"quiz_filter_{active_class.id}"
            )
            sel_quiz_id = None
            if sel_quiz_title != "Tüm quizler":
                sel_quiz_id = [q for q in quizzes if q.title == sel_quiz_title][0].id

            all_attempts = get_attempts_for_class(active_class.id)
            student_opts = ["Tümü"] + sorted({a["user_email"] for a in all_attempts})
            sel_student = st.selectbox(
                "Öğrenci",
                student_opts,
                index=0,
                key=f"student_filter_{active_class.id}",
            )
            sel_student_email = None if sel_student == "Tümü" else sel_student

            col_a, col_b = st.columns(2)
            with col_a:
                date_range = st.date_input(
                    "Tarih aralığı", key=f"date_filter_{active_class.id}"
                )
            with col_b:
                if st.button("Filtrele"):
                    st.rerun()

            since = None
            until = None
            if isinstance(date_range, list) and len(date_range) == 2:
                since = date_range[0].isoformat()
                until = date_range[1].isoformat()

            attempts = get_attempts_for_class(
                active_class.id,
                quiz_id=sel_quiz_id,
                user_email=sel_student_email,
                since=since,
                until=until,
            )

            if attempts:
                if st.button("CSV indir (Filtreli)"):
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(
                        [
                            "attempt_id",
                            "quiz_title",
                            "user_email",
                            "score",
                            "max_score",
                            "finished_at",
                        ]
                    )
                    for a in attempts:
                        writer.writerow(
                            [
                                a["attempt_id"],
                                a["quiz_title"],
                                a["user_email"],
                                a["score"],
                                a["max_score"],
                                a["finished_at"],
                            ]
                        )
                    st.download_button(
                        "CSV indir",
                        data=output.getvalue(),
                        file_name=f"attempts_class_{active_class.code}_filtered.csv",
                        mime="text/csv",
                    )

                for a in attempts:
                    with st.expander(
                        f"{format_compact_time(a['finished_at'])} | {a['user_email']} | "
                        f"{a['quiz_title']} | {format_score(a['score'], a['max_score'])}"
                    ):
                        st.write(f"Attempt ID: {a['attempt_id']}")
                        det = get_attempt_detail(a["attempt_id"])
                        if det:
                            for pq in det["per_question"]:
                                st.write(
                                    f"- ({'Doğru' if pq['correct'] else 'Yanlış'}) "
                                    f"{pq['question_text']} [{pq['points']}]"
                                )
            else:
                st.info("Henüz deneme yok.")

        with tab_reports:
            st.subheader("Konu Başarı Durumu")
            topic_stats = compute_topic_mastery(active_class.id)
            if topic_stats:
                for topic, data in topic_stats.items():
                    st.write(
                        f"- **{topic}**: %{data['mastery']*100:.1f} "
                        f"({data['correct']}/{data['attempts']})"
                    )
                weak = [
                    t
                    for t, d in topic_stats.items()
                    if d["attempts"] >= 3 and d["mastery"] < 0.6
                ]
                if weak:
                    st.warning("Zayıf konular: " + ", ".join(weak))
                st.markdown("---")
                chart_data = {k: v["mastery"] * 100 for k, v in topic_stats.items()}
                st.bar_chart(list(chart_data.values()), use_container_width=True)
            else:
                st.info("Henüz deneme verisi yok.")

        st.markdown("---")
        st.subheader("Otomatik Quiz Kaydet")
        if st.session_state.quiz_questions:
            save_title = st.text_input("Quiz Başlığı")
            if st.button("Quizi Kaydet"):
                try:
                    qlist = []
                    for gq in st.session_state.quiz_questions:
                        qtype = gq.get("type") or gq.get("question_type") or "mcq"
                        if qtype in ("multiple_choice", "mcq"):
                            choices = {k: v for k, v in gq.items() if k in ("A", "B", "C", "D")}
                            correct = gq.get("correct_answer") or gq.get("correct")
                            qlist.append(
                                {
                                    "type": "mcq",
                                    "text": gq.get("question") or gq.get("question_text"),
                                    "choices": choices,
                                    "correct_answer": correct,
                                    "topics": gq.get("topics", []),
                                    "points": 1.0,
                                }
                            )
                        elif qtype == "true_false":
                            qlist.append(
                                {
                                    "type": "true_false",
                                    "text": gq.get("statement") or gq.get("question"),
                                    "correct_answer": gq.get("correct_answer"),
                                    "points": 1.0,
                                }
                            )
                        elif qtype == "fill_blank":
                            qlist.append(
                                {
                                    "type": "fill_blank",
                                    "text": gq.get("sentence"),
                                    "correct_answer": gq.get("correct_answer"),
                                    "points": 1.0,
                                }
                            )
                        else:
                            qlist.append(
                                {
                                    "type": "short_answer",
                                    "text": gq.get("question"),
                                    "correct_answer": gq.get("sample_answer")
                                    or gq.get("correct_answer"),
                                    "topics": gq.get("keywords", []),
                                    "points": 1.0,
                                }
                            )

                    created = create_quiz(
                        active_class.id,
                        save_title or "Yeni Quiz",
                        st.session_state.user["id"],
                        qlist,
                    )
                    st.success(f"Quiz kaydedildi: {created.title}")
                    st.session_state.quiz_questions = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
        else:
            st.info("Kaydetmek için önce quiz oluştur.")

        if active_class.owner_id == st.session_state.user.get("id"):
            st.markdown("---")
            st.subheader("Sınıfı Sil")
            st.warning("Bu işlem geri alınamaz ve sınıfa ait quizler silinir.")
            confirm_delete = st.checkbox(
                "Sınıfı silmeyi onaylıyorum", key="confirm_delete_class"
            )
            if st.button("Sınıfı Sil", type="secondary"):
                if not confirm_delete:
                    st.error("Silme işlemi için onay gerekli.")
                else:
                    try:
                        delete_class(active_class.id, st.session_state.user.get("id"))
                        st.success("Sınıf ve ilişkili veriler silindi.")
                        st.session_state.show_class_detail = False
                        st.session_state.selected_class_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")

else:
    st.markdown(
        """
        <div class="hero">
            <h2>Sınıflar</h2>
            <p>Üyesi olduğun sınıfları kartlar halinde görüntüle.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not classes:
        st.info("Henüz bir sınıfa katılmadın veya oluşturmadın.")

    cols = st.columns(3)
    card_index = 0

    with cols[card_index % 3]:
        if st.button("➕", key="create_or_join", use_container_width=True):
            if user_role == "teacher":
                st.switch_page("pages/6_Sinif_Olustur.py")
            else:
                st.session_state.show_join_form = True
                st.rerun()
    card_index += 1

    for cls in classes:
        with cols[card_index % 3]:
            label = f"{cls.title}\n{cls.code}"
            if st.button(label, key=f"class_card_{cls.id}", use_container_width=True):
                st.session_state.selected_class_id = cls.id
                st.session_state.show_class_detail = True
                st.session_state.last_class_id = cls.id
                st.rerun()
        card_index += 1

    if user_role == "student" and st.session_state.get("show_join_form"):
        st.markdown("---")
        st.subheader("Sınıfa Katıl")
        join_code = st.text_input("Davet kodu")
        if st.button("Katıl"):
            try:
                enrollment = join_class_by_code(join_code, st.session_state.user["id"])
                st.session_state.selected_class_id = enrollment.class_id
                st.session_state.show_class_detail = True
                st.session_state.last_class_id = enrollment.class_id
                st.session_state.show_join_form = False
                st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")

if st.session_state.get("current_attempt"):
    attempt = st.session_state.current_attempt
    st.markdown("---")
    st.subheader("Quiz Denemesi")
    for q in attempt["questions"]:
        st.write(f"**{q['text']}**")
        if q["type"] == "mcq":
            choices = q.get("choices") or {}
            st.radio(
                f"Seçim {q['id']}",
                options=list(choices.keys()),
                key=f"ans_{q['id']}",
                format_func=lambda opt, c=choices: f"{opt}) {c.get(opt, '')}" if c else opt,
            )
        elif q["type"] == "true_false":
            st.selectbox(
                f"Doğru/Yanlış {q['id']}",
                options=["True", "False"],
                key=f"ans_{q['id']}",
            )
        elif q["type"] == "fill_blank":
            st.text_input(f"Cevap {q['id']}", key=f"ans_{q['id']}")
        else:
            st.text_area(f"Cevap {q['id']}", key=f"ans_{q['id']}")

    if st.button("Denemeyi Bitir"):
        gathered = []
        for q in attempt["questions"]:
            a = st.session_state.get(f"ans_{q['id']}")
            gathered.append({"question_id": q["id"], "answer": a})
        try:
            res = grade_attempt(attempt["quiz_id"], st.session_state.user["id"], gathered)
            st.success(f"Puan: {format_score(res['score'], res['max_score'])}")
            for pqres in res["per_question"]:
                st.write(
                    f"Soru {pqres['question_id']}: "
                    f"{'Doğru' if pqres['correct'] else 'Yanlış'}"
                )
            st.session_state.current_attempt = None
            st.rerun()
        except Exception as e:
            st.error(f"Hata: {e}")
