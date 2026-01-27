import json
import io
import csv
import logging
import pandas as pd
import altair as alt
from datetime import datetime

import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.classes import join_class_by_code, get_user_classes, delete_class, update_class
from utils.quiz import (
    get_quizzes_for_class,
    create_quiz,
    publish_quiz,
    get_questions_for_quiz,
    grade_attempt,
    get_attempt_count,
    delete_attempt,
    delete_quiz,
    compute_topic_mastery,
    get_attempts_for_class,
    get_attempt_detail,
)

logger = logging.getLogger(__name__)

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
    st.markdown(
        f"<div style='text-align:right;color:#80ed99;font-weight:600;'>"
        f"Sınıf Kodu: {active_class.code}</div>",
        unsafe_allow_html=True,
    )

    if user_role == "student":
        last_result = st.session_state.get("last_attempt_result")
        if last_result and last_result.get("class_id") == active_class.id:
            st.markdown("---")
            st.subheader("Son Deneme Sonucu")
            st.success(
                f"Puan: {format_score(last_result['score'], last_result['max_score'])}"
            )
            for idx, pqres in enumerate(last_result.get("per_question", []), start=1):
                st.write(
                    f"Soru {idx}: "
                    f"{'Doğru' if pqres['correct'] else 'Yanlış'}"
                )

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
                    attempt_count = get_attempt_count(pq.id, st.session_state.user["id"])
                    if attempt_count >= 2:
                        st.warning("Bu quiz için deneme hakkınız doldu (2/2).")
                    if st.button(
                        "Quiz'e Katıl",
                        key=f"att_{pq.id}",
                        disabled=attempt_count >= 2,
                    ):
                        qs = get_questions_for_quiz(pq.id)
                        st.session_state.current_attempt = {
                            "quiz_id": pq.id,
                            "class_id": active_class.id,
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
                        st.session_state.last_attempt_result = None
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
                col_left, col_right = st.columns([0.9, 0.1])
                with col_left:
                    with st.expander(
                        f"{format_compact_time(a['finished_at'])} | {a['quiz_title']} | "
                        f"{format_score(a['score'], a['max_score'])}"
                    ):
                        det = get_attempt_detail(a["attempt_id"])
                        if det:
                            for idx, pq in enumerate(det["per_question"], start=1):
                                st.write(
                                    f"- Soru {idx} "
                                    f"({'Doğru' if pq['correct'] else 'Yanlış'}) "
                                    f"{pq['question_text']} [{pq['points']}]"
                                )
                with col_right:
                    if st.button("\U0001F5D1", key=f"del_attempt_{a['attempt_id']}", help="Denemeyi sil"):
                        try:
                            delete_attempt(a["attempt_id"], st.session_state.user["id"])
                            st.session_state.last_attempt_result = None
                            st.rerun()
                        except Exception:
                            logger.exception("Deneme silme hatasi")
                            st.error("Islem tamamlanamadi. Lutfen tekrar deneyin.")
        else:
            st.info("Henüz deneme yok.")

    else:
        quizzes = get_quizzes_for_class(active_class.id)
        tab_quiz, tab_students, tab_attempts, tab_reports, tab_admin = st.tabs(
            ["Quiz Yönetimi", "Öğrenciler", "Denemeler", "Raporlar", "Sınıf Yönetimi"]
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
                        col_a, col_b, col_c = st.columns([1, 1, 0.2])
                        with col_a:
                            if st.button(
                                "Yayınla" if not q.published else "Yayını Kapat",
                                key=f"pub_{q.id}",
                            ):
                                try:
                                    publish_quiz(q.id, publish=not q.published)
                                    st.success("Durum güncellendi")
                                    st.rerun()
                                except Exception:
                                    logger.exception("Quiz silme hatasi")
                                    st.error("Islem tamamlanamadi. Lutfen tekrar deneyin.")
                        with col_b:
                            if st.button("Soruları Görüntüle", key=f"view_{q.id}"):
                                questions = get_questions_for_quiz(q.id)
                                for idx, qq in enumerate(questions, start=1):
                                    st.write(f"- Soru {idx} ({qq.type}) {qq.text} [{qq.points} puan]")
                        with col_c:
                            if st.button("\U0001F5D1", key=f"del_quiz_{q.id}", help="Quizi sil"):
                                try:
                                    delete_quiz(q.id, st.session_state.user["id"])
                                    st.success("Quiz silindi.")
                                    st.rerun()
                                except Exception:
                                    logger.exception("Quiz yayinlama hatasi")
                                    st.error("Islem tamamlanamadi. Lutfen tekrar deneyin.")
            else:
                st.info("Henüz bu sınıfa ait quiz yok.")

            st.markdown("---")
            st.subheader("Yay\u0131nlanmam\u0131\u015f Quizler")
            unpublished_quizzes = [q for q in quizzes if not q.published]
            unpublished_quizzes = sorted(
                unpublished_quizzes, key=lambda q: q.created_at or datetime.min, reverse=True
            )
            if unpublished_quizzes:
                for q in unpublished_quizzes:
                    st.write(f"- {q.title} ({format_compact_time(q.created_at)})")
            else:
                st.info("Hen\u00fcz yay\u0131nlanmam\u0131\u015f bir quiz yok.")

        with tab_students:
            st.subheader("Öğrenci Listesi")
            attempts_all = get_attempts_for_class(active_class.id, best_only=True)
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

            all_attempts = get_attempts_for_class(active_class.id, best_only=True)
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
                best_only=True,
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
                            for idx, pq in enumerate(det["per_question"], start=1):
                                st.write(
                                    f"- Soru {idx} "
                                    f"({'Doğru' if pq['correct'] else 'Yanlış'}) "
                                    f"{pq['question_text']} [{pq['points']}]"
                                )
            else:
                st.info("Henüz deneme yok.")

        with tab_reports:
            st.subheader("Raporlar")

            class_labels = {f"{c.title} ({c.code})": c for c in classes}
            class_keys = list(class_labels.keys())
            current_label = None
            for label, cls in class_labels.items():
                if cls.id == active_class.id:
                    current_label = label
                    break
            class_index = class_keys.index(current_label) if current_label in class_keys else 0

            col_a, col_b, col_c, col_d = st.columns([1.2, 1, 1, 1])
            with col_a:
                sel_class = st.selectbox(
                    "Sınıf",
                    class_keys,
                    index=class_index,
                    key=f"report_class_{active_class.id}",
                )
            with col_b:
                quiz_opts = ["Tüm quizler"] + [q.title for q in quizzes]
                sel_quiz_title = st.selectbox(
                    "Quiz",
                    quiz_opts,
                    index=0,
                    key=f"report_quiz_{active_class.id}",
                )
            with col_c:
                attempts_all = get_attempts_for_class(
                    active_class.id,
                    quiz_id=None if sel_quiz_title == "Tüm quizler" else [q for q in quizzes if q.title == sel_quiz_title][0].id,
                    best_only=True,
                )
                student_opts = ["Tümü"] + sorted({a["user_email"] for a in attempts_all if a.get("user_email")})
                sel_student = st.selectbox(
                    "Öğrenci",
                    student_opts,
                    index=0,
                    key=f"report_student_{active_class.id}",
                )
            with col_d:
                date_range = st.date_input("Tarih aralığı", key=f"report_date_{active_class.id}")

            if class_labels.get(sel_class) and class_labels[sel_class].id != active_class.id:
                st.session_state.selected_class_id = class_labels[sel_class].id
                st.session_state.show_class_detail = True
                st.rerun()

            sel_quiz_id = None
            if sel_quiz_title != "Tüm quizler":
                sel_quiz_id = [q for q in quizzes if q.title == sel_quiz_title][0].id

            sel_student_email = None if sel_student == "Tümü" else sel_student

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
                best_only=True,
            )

            if not attempts:
                st.info("Henüz deneme verisi yok.")
            else:
                total_score = sum(a.get("score") or 0 for a in attempts)
                total_max = sum(a.get("max_score") or 0 for a in attempts)
                avg_rate = (total_score / total_max) * 100 if total_max else 0.0

                topic_stats = compute_topic_mastery(active_class.id, attempts=attempts)
                strongest = None
                weakest = None
                if topic_stats:
                    strongest = max(topic_stats.items(), key=lambda x: x[1].get("mastery", 0))
                    weakest = min(topic_stats.items(), key=lambda x: x[1].get("mastery", 0))

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Ortalama başarı", f"%{avg_rate:.1f}")
                k2.metric("Deneme sayısı", str(len(attempts)))
                k3.metric("En güçlü konu", strongest[0] if strongest else "-")
                k4.metric("En zayıf konu", weakest[0] if weakest else "-")

                st.markdown("---")
                if topic_stats:
                    topic_rows = []
                    for topic, data in topic_stats.items():
                        topic_rows.append({
                            "Konu": topic,
                            "Başarı (%)": round(data["mastery"] * 100, 1),
                            "Doğru": data["correct"],
                            "Deneme": data["attempts"],
                        })
                    topic_df = pd.DataFrame(topic_rows).sort_values("Başarı (%)", ascending=False)
                    st.subheader("Konu bazlı ısı haritası")
                    st.dataframe(
                        topic_df.style.background_gradient(cmap="Greens", subset=["Başarı (%)"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Konu başarı verisi bulunamadı.")

                st.markdown("---")
                st.subheader("Öğrenci segmentleri")
                student_stats = {}
                for a in attempts:
                    key = a.get("user_email") or a.get("user_id")
                    if key not in student_stats:
                        student_stats[key] = {
                            "name": a.get("user_full_name") or a.get("user_email") or str(a.get("user_id")),
                            "score": 0.0,
                            "max_score": 0.0,
                            "attempts": 0,
                        }
                    student_stats[key]["score"] += a.get("score") or 0.0
                    student_stats[key]["max_score"] += a.get("max_score") or 0.0
                    student_stats[key]["attempts"] += 1

                seg_rows = []
                for item in student_stats.values():
                    rate = (item["score"] / item["max_score"]) * 100 if item["max_score"] else 0.0
                    if rate < 50:
                        seg = "Riskli"
                    elif rate < 75:
                        seg = "Orta"
                    else:
                        seg = "İyi"
                    seg_rows.append({
                        "Öğrenci": item["name"],
                        "Başarı (%)": round(rate, 1),
                        "Deneme": item["attempts"],
                        "Segment": seg,
                    })

                if seg_rows:
                    seg_df = pd.DataFrame(seg_rows).sort_values("Başarı (%)", ascending=False)
                    st.dataframe(seg_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Öğrenci segmenti için yeterli veri yok.")

            st.markdown("---")
            st.subheader("Zaman trendi")
            trend_rows = []
            for a in attempts:
                finished = a.get("finished_at")
                if not finished:
                    continue
                try:
                    dt = datetime.fromisoformat(str(finished))
                except Exception:
                    continue
                trend_rows.append({
                    "date": dt.date(),
                    "score": a.get("score") or 0.0,
                    "max_score": a.get("max_score") or 0.0,
                })

            if trend_rows:
                trend_df = pd.DataFrame(trend_rows)
                trend_df["rate"] = trend_df.apply(
                    lambda r: (r["score"] / r["max_score"] * 100) if r["max_score"] else 0.0, axis=1
                )
                grouped = trend_df.groupby("date").agg(
                    avg_rate=("rate", "mean"),
                    attempts=("rate", "count"),
                ).reset_index()
                grouped = grouped.sort_values("date")
                grouped["date"] = pd.to_datetime(grouped["date"])

                line = alt.Chart(grouped).mark_line(color="#58a6ff", strokeWidth=2).encode(
                    x=alt.X("date:T", title="Tarih", axis=alt.Axis(labelAngle=-30)),
                    y=alt.Y(
                        "avg_rate:Q",
                        title="Ortalama ba\u015far\u0131 (%)",
                        scale=alt.Scale(domain=[0, 100]),
                    ),
                    tooltip=[
                        alt.Tooltip("date:T", title="Tarih"),
                        alt.Tooltip("avg_rate:Q", title="Ortalama ba\u015far\u0131 (%)", format=".1f"),
                        alt.Tooltip("attempts:Q", title="Deneme say\u0131s\u0131"),
                    ],
                ).properties(height=220)
                bars = alt.Chart(grouped).mark_bar(color="#f2a365", opacity=0.35).encode(
                    x=alt.X("date:T", title=None),
                    y=alt.Y(
                        "attempts:Q",
                        title="Deneme say\u0131s\u0131",
                        axis=alt.Axis(orient="right"),
                    ),
                    tooltip=[
                        alt.Tooltip("date:T", title="Tarih"),
                        alt.Tooltip("attempts:Q", title="Deneme say\u0131s\u0131"),
                    ],
                ).properties(height=220)

                chart = (
                    alt.layer(bars, line)
                    .resolve_scale(y="independent")
                    .configure_view(
                        fill="#0b1220",
                        stroke=None,
                    )
                    .configure_axis(
                        labelColor="#c9d1d9",
                        titleColor="#c9d1d9",
                        gridColor="#1f2a3a",
                        domainColor="#1f2a3a",
                        tickColor="#1f2a3a",
                        labelFontSize=9,
                        titleFontSize=10,
                    )
                    .configure_title(color="#c9d1d9")
                )

                st.markdown(
                    '<div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;margin:2px 0 8px 0;"><span style="color:#58a6ff;">&bull; Ortalama başarı (%)</span><span style="color:#f2a365;">&bull; Deneme sayısı</span></div>',
                    unsafe_allow_html=True,
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Zaman trendi i\u00e7in yeterli veri yok.")

        with tab_admin:
            st.subheader("Sınıf Yönetimi")
            if active_class.owner_id != st.session_state.user.get("id"):
                st.info("Sınıf ayarlarını yalnızca sınıf sahibi güncelleyebilir.")
            else:
                new_title = st.text_input("Sınıf adı", value=active_class.title or "")
                new_desc = st.text_area("Sınıf açıklaması", value=active_class.description or "")
                if st.button("Güncelle"):
                    try:
                        update_class(active_class.id, st.session_state.user.get("id"), new_title, new_desc)
                        st.success("Sınıf bilgileri güncellendi.")
                        st.rerun()
                    except Exception:
                        logger.exception("Sınıf güncelleme hatası")
                        st.error("Sınıf bilgileri güncellenemedi. Lütfen tekrar deneyin.")

            st.markdown("---")
            st.subheader("Sınıfı Sil")
            st.warning("Bu işlem geri alınamaz ve sınıfa ait quizler silinir.")
            confirm_delete = st.checkbox("Sınıfı silmeyi onaylıyorum", key="confirm_delete_class")
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
                    except Exception:
                        logger.exception("Sinif silme hatasi")
                        st.error("Sinif silinemedi. Lutfen tekrar deneyin.")

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
                except Exception:
                    logger.exception("Quiz kaydetme hatasi (sinif sayfasi)")
                    st.error("Quiz kaydedilemedi. Lutfen tekrar deneyin.")

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
        if st.button("\u2795", key="create_or_join", use_container_width=True, help="Sinif olustur/katil"):
            if user_role == "teacher":
                st.switch_page("pages/6_Sinif_Olustur.py")
            else:
                st.session_state.show_join_form = True
                st.rerun()
    card_index += 1

    for cls in classes:
        with cols[card_index % 3]:
            label = f"{cls.title}"
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
            except Exception:
                logger.exception("Sinifa katilma hatasi")
                st.error("Sinifa katilinamadi. Lutfen tekrar deneyin.")

if st.session_state.get("current_attempt"):
    attempt = st.session_state.current_attempt
    st.markdown("---")
    st.subheader("Quiz Denemesi")
    for q in attempt["questions"]:
        st.write(f"**{q['text']}**")
        if q["type"] == "mcq":
            choices = q.get("choices") or {}
            st.radio(
                f"mcq_{q['id']}",
                options=list(choices.keys()),
                key=f"ans_{q['id']}",
                format_func=lambda opt, c=choices: f"{opt}) {c.get(opt, '')}" if c else opt,
                label_visibility="collapsed",
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
            st.session_state.last_attempt_result = {
                "class_id": attempt.get("class_id"),
                "score": res["score"],
                "max_score": res["max_score"],
                "per_question": res["per_question"],
            }
            st.session_state.current_attempt = None
            st.rerun()
        except Exception:
            logger.exception("Quiz deneme tamamlama hatasi")
            st.error("Deneme kaydedilemedi. Lutfen tekrar deneyin.")
