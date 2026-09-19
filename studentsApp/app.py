from datetime import datetime,date,time
from zoneinfo import ZoneInfo
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st

from streamlit_option_menu import option_menu

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle

from config import Config
from database import Database


st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon="./students_tracking_system_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


def now():
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    )


def initialize_session():
    defaults={
        "logged_in":False,
        "student":None,
        "department":None,
        "batch":None,
        "section":None,
        "roll_number":None,
        "semester":None,
        "logged_in_time":None,
        "logged_out_time":None,
        "overall_progress_start_time":None,
        "selected_subject":None,
        "selected_subject_start_time":None,
        "selected_subject_end_time":None,
        "subject_selector_version":0,
        "flash_message":None
    }

    for key,value in defaults.items():
        if key not in st.session_state:
            st.session_state[key]=value


def parse_date(value):
    if isinstance(value,datetime):
        return value.date()

    if isinstance(value,date):
        return value

    value=str(value or "").strip()

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z","+00:00")
        ).date()
    except:
        pass

    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d"
    ):
        try:
            return datetime.strptime(
                value,
                fmt
            ).date()
        except:
            pass

    return None


def time_text(value):
    if isinstance(value,datetime):
        return value.strftime(
            "%I:%M:%S %p"
        )

    if isinstance(value,time):
        return value.strftime(
            "%I:%M:%S %p"
        )

    value=str(value or "").strip()

    if not value:
        return "-"

    for fmt in (
        "%H:%M:%S",
        "%H:%M",
        "%I:%M:%S %p",
        "%I:%M %p"
    ):
        try:
            return datetime.strptime(
                value,
                fmt
            ).strftime(
                "%I:%M:%S %p"
            )
        except:
            pass

    return value


def clock_minutes(value):
    if isinstance(value,datetime):
        return (
            value.hour*60+
            value.minute+
            value.second/60
        )

    if isinstance(value,time):
        return (
            value.hour*60+
            value.minute+
            value.second/60
        )

    value=str(value or "").strip()

    for fmt in (
        "%H:%M:%S",
        "%H:%M",
        "%I:%M:%S %p",
        "%I:%M %p"
    ):
        try:
            parsed=datetime.strptime(
                value,
                fmt
            )

            return (
                parsed.hour*60+
                parsed.minute+
                parsed.second/60
            )

        except:
            pass

    return None


def numeric(value):
    try:
        return float(value)
    except:
        return 0.0


def duration_minutes(session,overall=False):
    if not isinstance(session,dict):
        return 0.0

    duration_seconds=session.get(
        "duration_seconds"
    )

    if duration_seconds is not None:
        try:
            return max(
                0,
                float(duration_seconds)/60
            )
        except:
            pass

    hours_field=(
        "hours_studied"
        if overall
        else "hours_spent"
    )

    hours=session.get(
        hours_field,
        0
    )

    minutes=session.get(
        "minutes_spent",
        0
    )

    if isinstance(hours,time):
        return (
            hours.hour*60+
            hours.minute+
            hours.second/60
        )

    hours_text=str(
        hours or ""
    ).strip()

    if ":" in hours_text:
        parts=hours_text.split(":")

        try:
            result=float(parts[0])*60

            if len(parts)>1:
                result+=float(parts[1])

            if len(parts)>2:
                result+=float(parts[2])/60

            return max(
                0,
                result
            )

        except:
            pass

    hour_value=numeric(hours)
    minute_value=numeric(minutes)

    if hour_value>0:
        return max(
            0,
            hour_value*60+
            minute_value
        )

    if minute_value>0:
        return max(
            0,
            minute_value
        )

    start=clock_minutes(
        session.get(
            "start_time"
        )
    )

    end=clock_minutes(
        session.get(
            "end_time"
        )
    )

    if (
        start is not None
        and
        end is not None
    ):
        if end<start:
            end+=1440

        return max(
            0,
            end-start
        )

    return 0.0


def duration_text(minutes):
    try:
        minutes=float(minutes)
    except:
        minutes=0

    if 0<minutes<1:
        return "<1m"

    minutes=max(
        0,
        int(round(minutes))
    )

    hours,remaining=divmod(
        minutes,
        60
    )

    return f"{hours}h {remaining}m"


def elapsed_minutes(start,end=None):
    if not start:
        return 0

    return max(
        0,
        (
            (end or now())-start
        ).total_seconds()/60
    )


def semester_number(value):
    try:
        value=int(value)

        if 1<=value<=8:
            return value

    except:
        pass

    text=str(
        value or ""
    )

    digits="".join(
        character
        for character in text
        if character.isdigit()
    )

    if digits:
        try:
            value=int(digits)

            if 1<=value<=8:
                return value
        except:
            pass

    return None


def task_total_marks(task):
    value=task.get(
        "total_marks"
    )

    if value is not None:
        try:
            return float(value)
        except:
            pass

    total=0.0

    for question in task.get(
        "questions",
        []
    ):
        total+=numeric(
            question.get(
                "marks"
            )
        )

    return total


def subject_sessions(
    activity,
    date_filter=None,
    semester_filter=None
):
    if not isinstance(
        activity,
        dict
    ):
        return []

    tracks=activity.get(
        "tracks",
        activity.get(
            "tarcks",
            []
        )
    )

    if isinstance(
        tracks,
        dict
    ):
        tracks=[tracks]

    rows=[]

    for track in tracks or []:
        semester=semester_number(
            track.get(
                "subject_semister",
                track.get(
                    "subject_semester"
                )
            )
        )

        if (
            semester_filter is not None
            and
            semester!=int(
                semester_filter
            )
        ):
            continue

        track_subjects=track.get(
            "track_subjects",
            []
        )

        if isinstance(
            track_subjects,
            dict
        ):
            track_subjects=[
                track_subjects
            ]

        for daily in track_subjects or []:
            current_date=parse_date(
                daily.get(
                    "date"
                )
            )

            if (
                date_filter
                and
                current_date!=date_filter
            ):
                continue

            sessions=daily.get(
                "sessions",
                daily.get(
                    "session",
                    []
                )
            )

            if isinstance(
                sessions,
                dict
            ):
                sessions=[
                    sessions
                ]

            for session in sessions or []:
                rows.append({
                    "Subject":track.get(
                        "subject_name",
                        ""
                    ),
                    "Semester":semester or "",
                    "Type":track.get(
                        "subject_type",
                        ""
                    ),
                    "Credits":track.get(
                        "subject_credits",
                        ""
                    ),
                    "Date":current_date,
                    "Start Time":time_text(
                        session.get(
                            "start_time"
                        )
                    ),
                    "End Time":time_text(
                        session.get(
                            "end_time"
                        )
                    ),
                    "Minutes":duration_minutes(
                        session
                    )
                })

    return rows


def daily_sessions(
    activity,
    date_filter=None
):
    if not isinstance(
        activity,
        dict
    ):
        return []

    track=activity.get(
        "track",
        []
    )

    if isinstance(
        track,
        dict
    ):
        track=[
            track
        ]

    rows=[]

    for daily in track or []:
        current_date=parse_date(
            daily.get(
                "date"
            )
        )

        if (
            date_filter
            and
            current_date!=date_filter
        ):
            continue

        sessions=daily.get(
            "sessions",
            daily.get(
                "session",
                []
            )
        )

        if isinstance(
            sessions,
            dict
        ):
            sessions=[
                sessions
            ]

        for session in sessions or []:
            rows.append({
                "Date":current_date,
                "Start Time":time_text(
                    session.get(
                        "start_time"
                    )
                ),
                "End Time":time_text(
                    session.get(
                        "end_time"
                    )
                ),
                "Minutes":duration_minutes(
                    session,
                    True
                )
            })

    return rows


@st.dialog(
    "Login First To Proceed",
    width="large",
    dismissible=False,
    icon="🔐"
)
def alert_dialog():
    st.video(
        Config.LOGIN_VIDEO_URL
    )

    try:
        Database.test()

    except Exception as error:
        st.error(
            f"Database connection failed: {error}"
        )
        return


    department=st.selectbox(
        "Select Department",
        Config.DEPARTMENTS,
        index=None,
        placeholder="Select department",
        key="login_department"
    )

    if not department:
        return


    try:
        batches=Database.student_batches(
            department
        )

    except Exception as error:
        st.error(
            f"Unable to fetch batches: {error}"
        )
        return


    if not batches:
        st.warning(
            "No batches available for this department."
        )
        return


    batch=st.selectbox(
        "Select Batch",
        batches,
        index=None,
        placeholder="Select batch",
        key=f"login_batch_{department}"
    )

    if not batch:
        return


    try:
        sections=Database.sections(
            department,
            batch
        )

    except Exception as error:
        st.error(
            f"Unable to fetch sections: {error}"
        )
        return


    if not sections:
        st.warning(
            "No sections available for this batch."
        )
        return


    section=st.selectbox(
        "Select Section",
        sections,
        index=None,
        placeholder="Select section",
        key=f"login_section_{department}_{batch}"
    )

    if not section:
        return


    try:
        students=Database.students_by_section(
            department,
            batch,
            section
        )

    except Exception as error:
        st.error(
            f"Unable to fetch students: {error}"
        )
        return


    students=sorted(
        students,
        key=lambda value:
        str(
            value.get(
                "student_roll_number",
                ""
            )
        )
    )


    rolls=[
        str(
            value.get(
                "student_roll_number"
            )
        )
        for value in students
        if value.get(
            "student_roll_number"
        )
    ]


    if not rolls:
        st.warning(
            "No students are available for this section."
        )
        return


    roll=st.selectbox(
        "Select Roll Number",
        rolls,
        index=None,
        placeholder="Select roll number",
        key=f"login_roll_{department}_{batch}_{section}"
    )

    if not roll:
        return


    student=Database.student(
        department,
        batch,
        section,
        roll
    )


    if not student:
        st.error(
            "Student account not found."
        )
        return


    semester=Database.student_semester(
        department,
        batch,
        section,
        roll
    )


    if semester is None:
        st.error(
            "Semister is missing or invalid in this student document."
        )

        st.write(
            "Expected MongoDB field:"
        )

        st.code(
            '"semister": 5'
        )

        return


    st.info(
        f"{student.get('student_name','Student')} "
        f"| Section {section} "
        f"| Semester {semester}"
    )


    with st.form(
        "login_form"
    ):
        password=st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login=st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True
        )


    if login:
        if not password:
            st.warning(
                "Enter your password."
            )
            return


        if str(
            student.get(
                "student_password",
                ""
            )
        )!=str(password):
            st.error(
                "Incorrect password."
            )
            return


        login_time=now()

        st.session_state.logged_in=True
        st.session_state.student=student

        st.session_state.department=department
        st.session_state.batch=batch
        st.session_state.section=section
        st.session_state.roll_number=roll
        st.session_state.semester=semester

        st.session_state.logged_in_time=login_time
        st.session_state.logged_out_time=None

        st.session_state.overall_progress_start_time=login_time

        st.session_state.selected_subject=None
        st.session_state.selected_subject_start_time=None
        st.session_state.selected_subject_end_time=None

        st.session_state.subject_selector_version+=1

        st.toast(
            "Successfully Logged In",
            icon="✅"
        )

        st.rerun()


def logout():
    for key in list(
        st.session_state.keys()
    ):
        del st.session_state[key]

    st.rerun()


def resolve_material_path(value):
    value=str(
        value or ""
    ).strip()

    if not value:
        return None


    if value.startswith(
        (
            "http://",
            "https://"
        )
    ):
        return value


    path=Path(value)

    students_app=Path(
        __file__
    ).resolve().parent

    project_root=students_app.parent

    cleaned=value.replace(
        "\\",
        "/"
    ).lstrip("./")


    candidates=[
        path,
        students_app/path,
        project_root/path,
        project_root/"controller_with_stats"/cleaned,
        project_root/"controller"/cleaned,
        Path.cwd()/path,
        Path.cwd().parent/path
    ]


    for candidate in candidates:
        try:
            if candidate.exists():
                return str(
                    candidate.resolve()
                )
        except:
            pass

    return None


def learn_page():
    subject=st.session_state.selected_subject

    if not subject:
        st.info(
            "Select a subject from the sidebar."
        )
        return


    curriculum=Database.curriculum(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.semester,
        subject,
        st.session_state.section
    )


    if not curriculum:
        st.warning(
            f"Curriculum is not available for "
            f"{subject} - Section "
            f"{st.session_state.section}."
        )
        return


    col1,col2=st.columns(
        [1,2],
        border=True,
        gap="small"
    )


    with col1:
        st.subheader(
            "Units"
        )

        unit=st.radio(
            "Select Unit",
            [
                "Unit 1",
                "Unit 2",
                "Unit 3",
                "Unit 4",
                "Unit 5"
            ],
            label_visibility="collapsed"
        )


    unit_number=unit.split()[-1]

    topics=curriculum.get(
        f"unit_{unit_number}",
        []
    )

    if isinstance(
        topics,
        dict
    ):
        topics=[
            topics
        ]


    with col2:
        st.subheader(
            f"{subject} - {unit}"
        )

        if not topics:
            st.info(
                "No topics available in this unit."
            )
            return


        names=[
            topic.get(
                "topic_name",
                "Untitled Topic"
            )
            for topic in topics
        ]


        selected=st.selectbox(
            "Select Topic",
            names
        )


        topic=topics[
            names.index(
                selected
            )
        ]


        yt_url=str(
            topic.get(
                "yt_url",
                ""
            )
        ).strip()


        if yt_url:
            st.video(
                yt_url
            )


        st.subheader(
            topic.get(
                "topic_name",
                ""
            )
        )


        st.write(
            topic.get(
                "description",
                "No description available."
            )
        )


def study_page():
    subject=st.session_state.selected_subject

    if not subject:
        st.info(
            "Select a subject from the sidebar."
        )
        return


    data=Database.subject_materials(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.semester,
        subject,
        st.session_state.section
    )


    if not data:
        st.warning(
            f"Materials are not available for "
            f"{subject} - Section "
            f"{st.session_state.section}."
        )
        return


    materials=data.get(
        "materials",
        []
    )

    if isinstance(
        materials,
        str
    ):
        materials=[
            materials
        ]


    if not materials:
        st.warning(
            "No materials are available for this subject."
        )
        return


    col1,col2=st.columns(
        [1,2],
        border=True,
        gap="small"
    )


    with col1:
        st.subheader(
            "Materials"
        )

        selected=st.selectbox(
            "Select Material",
            materials,
            format_func=lambda value:
            Path(
                str(value)
            ).name
        )

        resolved=resolve_material_path(
            selected
        )

        st.write(
            f"**File:** "
            f"{Path(str(selected)).name}"
        )


    with col2:
        st.subheader(
            Path(
                str(selected)
            ).name
        )


        if not resolved:
            st.error(
                f"Material file not found: {selected}"
            )
            return


        if str(
            resolved
        ).startswith(
            (
                "http://",
                "https://"
            )
        ):
            st.pdf(
                resolved,
                height=900
            )
            return


        if Path(
            resolved
        ).suffix.lower()!=".pdf":
            st.error(
                "Selected material is not a PDF file."
            )
            return


        st.pdf(
            resolved,
            height=900
        )


def student_track(task):
    roll=str(
        st.session_state.roll_number
    ).strip()

    section=str(
        st.session_state.section
    ).strip()


    tracks=task.get(
        "track",
        []
    )

    if isinstance(
        tracks,
        dict
    ):
        tracks=[
            tracks
        ]


    return next(
        (
            item
            for item in tracks
            if str(
                item.get(
                    "student_roll_number",
                    ""
                )
            ).strip()==roll
            and
            str(
                item.get(
                    "student_section",
                    ""
                )
            ).strip()==section
        ),
        None
    )


def option_map(question):
    return {
        "A":str(
            question.get(
                "option_a",
                ""
            )
        ),
        "B":str(
            question.get(
                "option_b",
                ""
            )
        ),
        "C":str(
            question.get(
                "option_c",
                ""
            )
        ),
        "D":str(
            question.get(
                "option_d",
                ""
            )
        )
    }


def correct_key(question):
    options=option_map(
        question
    )

    raw=str(
        question.get(
            "correct_option",
            ""
        )
    ).strip()

    value=raw.lower()


    aliases={
        "a":"A",
        "b":"B",
        "c":"C",
        "d":"D",
        "option a":"A",
        "option b":"B",
        "option c":"C",
        "option d":"D",
        "option_a":"A",
        "option_b":"B",
        "option_c":"C",
        "option_d":"D",
        "1":"A",
        "2":"B",
        "3":"C",
        "4":"D"
    }


    if value in aliases:
        return aliases[value]


    for key,text in options.items():
        if value==text.strip().lower():
            return key


    upper=raw.upper()

    if upper in options:
        return upper

    return ""


def task_report(task,track):
    buffer=BytesIO()

    document=SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4*cm,
        leftMargin=1.4*cm,
        topMargin=1.4*cm,
        bottomMargin=1.4*cm
    )

    styles=getSampleStyleSheet()


    title=ParagraphStyle(
        "TaskReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor(
            "#16325C"
        ),
        alignment=TA_CENTER,
        spaceAfter=18
    )


    heading=ParagraphStyle(
        "TaskReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor(
            "#16325C"
        ),
        spaceBefore=8,
        spaceAfter=6
    )


    body=ParagraphStyle(
        "TaskReportBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15
    )


    student=st.session_state.student

    total_marks=task_total_marks(
        task
    )


    story=[
        Paragraph(
            "Student Task Report",
            title
        )
    ]


    info=[
        [
            "Student Name",
            student.get(
                "student_name",
                ""
            ),
            "Roll Number",
            student.get(
                "student_roll_number",
                ""
            )
        ],
        [
            "Department",
            st.session_state.department,
            "Batch",
            st.session_state.batch
        ],
        [
            "Section",
            st.session_state.section,
            "Semester",
            str(
                st.session_state.semester
            )
        ],
        [
            "Subject",
            task.get(
                "subject_name",
                ""
            ),
            "Task",
            task.get(
                "task_name",
                ""
            )
        ],
        [
            "Uploaded Date",
            str(
                task.get(
                    "task_uploaded_date",
                    ""
                )
            ),
            "Status",
            track.get(
                "student_status",
                ""
            )
        ],
        [
            "Obtained Marks",
            str(
                track.get(
                    "student_marks",
                    0
                )
            ),
            "Total Marks",
            str(
                total_marks
            )
        ]
    ]


    table=Table(
        info,
        colWidths=[
            3.1*cm,
            5*cm,
            3.1*cm,
            5*cm
        ]
    )


    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0,0),
                (0,-1),
                colors.HexColor(
                    "#EAF2F8"
                )
            ),
            (
                "BACKGROUND",
                (2,0),
                (2,-1),
                colors.HexColor(
                    "#EAF2F8"
                )
            ),
            (
                "FONTNAME",
                (0,0),
                (0,-1),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (2,0),
                (2,-1),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0,0),
                (-1,-1),
                0.4,
                colors.HexColor(
                    "#B8C7D9"
                )
            ),
            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "TOP"
            ),
            (
                "PADDING",
                (0,0),
                (-1,-1),
                7
            )
        ])
    )


    story+=[
        table,
        Spacer(
            1,
            18
        ),
        Paragraph(
            "Question Details",
            heading
        )
    ]


    question_results=track.get(
        "question_results",
        []
    )


    for index,result in enumerate(
        question_results,
        1
    ):
        story.append(
            Paragraph(
                f"Question {index}",
                heading
            )
        )


        story.append(
            Paragraph(
                escape(
                    str(
                        result.get(
                            "question_name",
                            ""
                        )
                    )
                ),
                body
            )
        )


        data=[
            [
                "Selected Answer",
                Paragraph(
                    escape(
                        str(
                            result.get(
                                "selected_option",
                                "Not Answered"
                            )
                        )
                    ),
                    body
                )
            ],
            [
                "Correct Answer",
                Paragraph(
                    escape(
                        str(
                            result.get(
                                "correct_option",
                                ""
                            )
                        )
                    ),
                    body
                )
            ],
            [
                "Marks Awarded",
                (
                    f"{result.get('awarded_marks',0)} "
                    f"/ "
                    f"{result.get('marks',0)}"
                )
            ]
        ]


        question_table=Table(
            data,
            colWidths=[
                4*cm,
                12.2*cm
            ]
        )


        question_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0,0),
                    (0,-1),
                    colors.HexColor(
                        "#F4F6F7"
                    )
                ),
                (
                    "FONTNAME",
                    (0,0),
                    (0,-1),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.3,
                    colors.HexColor(
                        "#D5D8DC"
                    )
                ),
                (
                    "VALIGN",
                    (0,0),
                    (-1,-1),
                    "TOP"
                ),
                (
                    "PADDING",
                    (0,0),
                    (-1,-1),
                    6
                )
            ])
        )


        story+=[
            question_table,
            Spacer(
                1,
                12
            )
        ]


    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


def tasks_page():
    subject=st.session_state.selected_subject

    if not subject:
        st.info(
            "Select a subject from the sidebar."
        )
        return


    try:
        tasks=Database.student_tasks(
            st.session_state.department,
            st.session_state.batch,
            st.session_state.semester,
            subject,
            st.session_state.section,
            st.session_state.roll_number
        )

    except Exception as error:
        st.error(
            f"Unable to load tasks: {error}"
        )
        return


    if not tasks:
        st.warning(
            f"No tasks are available for "
            f"{subject} - Section "
            f"{st.session_state.section}."
        )
        return


    rows=[]


    for task in tasks:
        track=student_track(
            task
        )

        status=(
            track.get(
                "student_status",
                "Incomplete"
            )
            if track
            else "Incomplete"
        )

        rows.append({
            "Task Name":task.get(
                "task_name",
                ""
            ),
            "Uploaded Date":task.get(
                "task_uploaded_date",
                ""
            ),
            "Total Marks":task_total_marks(
                task
            ),
            "Status":(
                "✅ Completed"
                if str(status).lower()=="completed"
                else "❌ Incomplete"
            ),
            "Obtained Marks":(
                track.get(
                    "student_marks",
                    0
                )
                if track
                else 0
            )
        })


    col1,col2=st.columns(
        [1,2],
        border=True,
        gap="small"
    )


    with col1:
        st.subheader(
            "Tasks"
        )

        st.dataframe(
            pd.DataFrame(
                rows
            ),
            hide_index=True,
            use_container_width=True
        )


        labels=[
            (
                f"{task.get('task_name','Task')} "
                f"| "
                f"{task.get('task_uploaded_date','')}"
            )
            for task in tasks
        ]


        selected=st.selectbox(
            "Select Task",
            labels
        )


        task=tasks[
            labels.index(
                selected
            )
        ]


        track=student_track(
            task
        )


        if not track:
            st.error(
                "Your student tracking record is missing for this task."
            )

            st.caption(
                "Ask the controller/faculty to regenerate the task tracking list for this section."
            )

            return


        status=str(
            track.get(
                "student_status",
                "Incomplete"
            )
        )


        completed=(
            status.lower()
            =="completed"
        )


        total_marks=task_total_marks(
            task
        )


        st.write(
            f"**Status:** "
            f"{'✅ Completed' if completed else '❌ Incomplete'}"
        )

        st.write(
            f"**Total Marks:** {total_marks}"
        )


        if completed:
            st.write(
                f"**Marks Obtained:** "
                f"{track.get('student_marks',0)}"
            )


        attempt=st.toggle(
            "Attempt Task",
            disabled=completed,
            key=f"attempt_{task['_id']}"
        )


    with col2:
        st.subheader(
            task.get(
                "task_name",
                "Task"
            )
        )


        if completed:
            st.success(
                f"Task Completed | Marks: "
                f"{track.get('student_marks',0)} "
                f"/ {total_marks}"
            )


            report=task_report(
                task,
                track
            )


            safe_name=str(
                task.get(
                    "task_name",
                    "task"
                )
            ).replace(
                " ",
                "_"
            )


            st.download_button(
                "Download Report",
                report,
                file_name=(
                    f"{safe_name}_"
                    f"{st.session_state.roll_number}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )


            results=track.get(
                "question_results",
                []
            )


            if results:
                for index,result in enumerate(
                    results,
                    1
                ):
                    st.write(
                        f"**Q{index}. "
                        f"{result.get('question_name','')}**"
                    )

                    st.write(
                        f"Selected: "
                        f"{result.get('selected_option','Not Answered')}"
                    )

                    st.write(
                        f"Correct: "
                        f"{result.get('correct_option','')}"
                    )

                    st.write(
                        f"Marks: "
                        f"{result.get('awarded_marks',0)} "
                        f"/ "
                        f"{result.get('marks',0)}"
                    )

            return


        if not attempt:
            st.info(
                "Turn on Attempt Task to answer this task."
            )
            return


        questions=task.get(
            "questions",
            []
        )


        if not questions:
            st.warning(
                "This task has no questions."
            )
            return


        answers={}


        with st.form(
            f"task_form_{task['_id']}"
        ):
            for index,question in enumerate(
                questions
            ):
                st.write(
                    f"**Question {index+1}: "
                    f"{question.get('question_name','')}**"
                )


                st.caption(
                    f"Marks: "
                    f"{question.get('marks',0)}"
                )


                options=option_map(
                    question
                )


                keys=[
                    key
                    for key,value in options.items()
                    if str(value).strip()
                ]


                answers[index]=st.radio(
                    "Select Answer",
                    keys,
                    index=None,
                    format_func=lambda key:
                    f"{key}. {options[key]}",
                    key=(
                        f"answer_"
                        f"{task['_id']}_"
                        f"{index}"
                    )
                )


            submit=st.form_submit_button(
                "Submit Task",
                type="primary",
                use_container_width=True
            )


        if submit:
            total=0.0

            selected_answers=[]

            results=[]


            for index,question in enumerate(
                questions
            ):
                selected_key=answers.get(
                    index
                )

                correct=correct_key(
                    question
                )

                marks=float(
                    question.get(
                        "marks",
                        0
                    )
                    or 0
                )


                awarded=(
                    marks
                    if (
                        selected_key
                        and
                        selected_key==correct
                    )
                    else 0
                )


                total+=awarded


                options=option_map(
                    question
                )


                selected_text=options.get(
                    selected_key,
                    "Not Answered"
                )


                correct_text=options.get(
                    correct,
                    str(
                        question.get(
                            "correct_option",
                            ""
                        )
                    )
                )


                selected_answers.append({
                    "question_number":index+1,
                    "selected_key":selected_key,
                    "selected_option":selected_text
                })


                results.append({
                    "question_number":index+1,
                    "question_name":question.get(
                        "question_name",
                        ""
                    ),
                    "selected_key":selected_key,
                    "selected_option":selected_text,
                    "correct_key":correct,
                    "correct_option":correct_text,
                    "marks":marks,
                    "awarded_marks":awarded
                })


            try:
                result=Database.complete_task(
                    st.session_state.department,
                    st.session_state.batch,
                    st.session_state.semester,
                    subject,
                    st.session_state.section,
                    task["_id"],
                    st.session_state.roll_number,
                    total,
                    selected_answers,
                    results
                )

            except Exception as error:
                st.error(
                    f"Unable to submit task: {error}"
                )
                return


            if (
                result
                and
                result.modified_count
            ):
                st.success(
                    f"Task submitted successfully. "
                    f"Marks: {total} / {total_marks}"
                )

                st.rerun()

            else:
                st.error(
                    "Unable to update task. "
                    "The matching tracking record may not exist."
                )


def my_profile():
    student=st.session_state.student

    st.subheader(
        "My Profile"
    )


    c1,c2=st.columns(
        2
    )


    with c1:
        st.write(
            "**Student Name**"
        )

        st.write(
            student.get(
                "student_name",
                "-"
            )
        )


        st.write(
            "**Roll Number**"
        )

        st.write(
            student.get(
                "student_roll_number",
                "-"
            )
        )


        st.write(
            "**Gender**"
        )

        st.write(
            student.get(
                "student_gender",
                "-"
            )
        )


        st.write(
            "**Semester**"
        )

        st.write(
            st.session_state.semester
        )


    with c2:
        st.write(
            "**Department**"
        )

        st.write(
            st.session_state.department
        )


        st.write(
            "**Batch**"
        )

        st.write(
            st.session_state.batch
        )


        st.write(
            "**Section**"
        )

        st.write(
            st.session_state.section
        )


    st.subheader(
        "Change Password"
    )


    with st.form(
        "change_password_form"
    ):
        current=st.text_input(
            "Current Password",
            type="password"
        )

        new=st.text_input(
            "New Password",
            type="password"
        )

        confirm=st.text_input(
            "Confirm New Password",
            type="password"
        )

        change=st.form_submit_button(
            "Change Password",
            type="primary"
        )


    if change:
        latest=Database.student(
            st.session_state.department,
            st.session_state.batch,
            st.session_state.section,
            st.session_state.roll_number
        )


        if not current or not new or not confirm:
            st.warning(
                "Fill all password fields."
            )


        elif not latest:
            st.error(
                "Student account was not found."
            )


        elif str(
            latest.get(
                "student_password",
                ""
            )
        )!=current:
            st.error(
                "Current password is incorrect."
            )


        elif len(new)<4:
            st.warning(
                "New password must contain at least 4 characters."
            )


        elif new!=confirm:
            st.error(
                "New passwords do not match."
            )


        elif current==new:
            st.warning(
                "New password must be different from current password."
            )


        else:
            result=Database.change_password(
                st.session_state.department,
                st.session_state.batch,
                st.session_state.section,
                st.session_state.roll_number,
                new
            )


            if result.modified_count:
                st.session_state.student[
                    "student_password"
                ]=new

                st.success(
                    "Password changed successfully."
                )

            else:
                st.error(
                    "Password was not changed."
                )


def today_study_time():
    today=now().date()


    subject_activity=Database.student_subject_activity(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.section,
        st.session_state.roll_number
    )


    daily_activity=Database.student_daily_activity(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.section,
        st.session_state.roll_number
    )


    sessions=subject_sessions(
        subject_activity,
        today,
        st.session_state.semester
    )


    overall_sessions=daily_sessions(
        daily_activity,
        today
    )


    subjects=Database.theory_subjects(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.semester,
        st.session_state.section
    )


    summary={
        subject:{
            "Subject":subject,
            "Sessions":0,
            "Minutes":0,
            "Progress Saved":"Not Saved"
        }
        for subject in subjects
    }


    for session in sessions:
        subject=session[
            "Subject"
        ]


        if subject not in summary:
            summary[subject]={
                "Subject":subject,
                "Sessions":0,
                "Minutes":0,
                "Progress Saved":"Not Saved"
            }


        summary[subject][
            "Sessions"
        ]+=1


        summary[subject][
            "Minutes"
        ]+=session[
            "Minutes"
        ]


        summary[subject][
            "Progress Saved"
        ]="Saved"


    c1,c2,c3,c4=st.columns(
        4
    )


    c1.metric(
        "Subject Study Time",
        duration_text(
            sum(
                row["Minutes"]
                for row in sessions
            )
        )
    )


    c2.metric(
        "Overall Study Time",
        duration_text(
            sum(
                row["Minutes"]
                for row in overall_sessions
            )
        )
    )


    c3.metric(
        "Subject Sessions",
        len(
            sessions
        )
    )


    c4.metric(
        "Overall Sessions",
        len(
            overall_sessions
        )
    )


    st.subheader(
        f"Semester "
        f"{st.session_state.semester} "
        f"Subject-wise Study"
    )


    rows=[
        {
            "Subject":value["Subject"],
            "Sessions":value["Sessions"],
            "Time Spent":duration_text(
                value["Minutes"]
            ),
            "Progress Saved":value[
                "Progress Saved"
            ]
        }
        for value in summary.values()
    ]


    if rows:
        st.dataframe(
            pd.DataFrame(
                rows
            ),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info(
            "No subjects are available."
        )


    if summary:
        selected=st.selectbox(
            "View Subject Sessions",
            list(
                summary.keys()
            )
        )


        selected_sessions=[
            session
            for session in sessions
            if session["Subject"]==selected
        ]


        st.write(
            f"**Subject Progress:** "
            f"{'Saved' if selected_sessions else 'Not Saved'}"
        )


        st.write(
            f"**Total Time Today:** "
            f"{duration_text(sum(row['Minutes'] for row in selected_sessions))}"
        )


        if selected_sessions:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Start Time":row[
                            "Start Time"
                        ],
                        "End Time":row[
                            "End Time"
                        ],
                        "Time Spent":duration_text(
                            row[
                                "Minutes"
                            ]
                        )
                    }
                    for row in selected_sessions
                ]),
                hide_index=True,
                use_container_width=True
            )

        else:
            st.info(
                "No saved sessions for this subject today."
            )


    st.subheader(
        "Today's Overall Sessions"
    )


    if overall_sessions:
        st.dataframe(
            pd.DataFrame([
                {
                    "Start Time":row[
                        "Start Time"
                    ],
                    "End Time":row[
                        "End Time"
                    ],
                    "Time Spent":duration_text(
                        row[
                            "Minutes"
                        ]
                    )
                }
                for row in overall_sessions
            ]),
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info(
            "Overall study progress has not been saved today."
        )


def overall_study_time():
    subject_activity=Database.student_subject_activity(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.section,
        st.session_state.roll_number
    )


    daily_activity=Database.student_daily_activity(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.section,
        st.session_state.roll_number
    )


    sessions=subject_sessions(
        subject_activity
    )


    overall_sessions=daily_sessions(
        daily_activity
    )


    days={
        row["Date"]
        for row in overall_sessions
        if row["Date"]
    }


    if not days:
        days={
            row["Date"]
            for row in sessions
            if row["Date"]
        }


    c1,c2,c3,c4=st.columns(
        4
    )


    c1.metric(
        "Total Subject Study",
        duration_text(
            sum(
                row["Minutes"]
                for row in sessions
            )
        )
    )


    c2.metric(
        "Overall Study Time",
        duration_text(
            sum(
                row["Minutes"]
                for row in overall_sessions
            )
        )
    )


    c3.metric(
        "Total Sessions",
        len(
            overall_sessions
        )
    )


    c4.metric(
        "Study Days",
        len(
            days
        )
    )


    st.subheader(
        "Overall Subject-wise Study"
    )


    grouped={}


    for session in sessions:
        key=(
            session["Semester"],
            session["Subject"]
        )


        if key not in grouped:
            grouped[key]={
                "Semester":session[
                    "Semester"
                ],
                "Subject":session[
                    "Subject"
                ],
                "Minutes":0,
                "Sessions":0,
                "Dates":set()
            }


        grouped[key][
            "Minutes"
        ]+=session[
            "Minutes"
        ]


        grouped[key][
            "Sessions"
        ]+=1


        if session["Date"]:
            grouped[key][
                "Dates"
            ].add(
                session["Date"]
            )


    rows=[
        {
            "Semester":value[
                "Semester"
            ],
            "Subject":value[
                "Subject"
            ],
            "Sessions":value[
                "Sessions"
            ],
            "Study Days":len(
                value[
                    "Dates"
                ]
            ),
            "Total Time":duration_text(
                value[
                    "Minutes"
                ]
            )
        }
        for value in grouped.values()
    ]


    if rows:
        st.dataframe(
            pd.DataFrame(
                rows
            ),
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info(
            "No subject-wise study history available."
        )


    if grouped:
        keys=list(
            grouped.keys()
        )


        labels=[
            f"Semester {key[0]} - {key[1]}"
            for key in keys
        ]


        selected=st.selectbox(
            "View Subject History",
            labels
        )


        key=keys[
            labels.index(
                selected
            )
        ]


        details=[
            row
            for row in sessions
            if (
                row["Semester"],
                row["Subject"]
            )==key
        ]


        st.dataframe(
            pd.DataFrame([
                {
                    "Date":(
                        row["Date"].strftime(
                            "%d-%m-%Y"
                        )
                        if row["Date"]
                        else "-"
                    ),
                    "Start Time":row[
                        "Start Time"
                    ],
                    "End Time":row[
                        "End Time"
                    ],
                    "Time Spent":duration_text(
                        row[
                            "Minutes"
                        ]
                    )
                }
                for row in details
            ]),
            hide_index=True,
            use_container_width=True
        )


    st.subheader(
        "Overall Daily Study History"
    )


    daily_group={}


    for session in overall_sessions:
        key=session[
            "Date"
        ]


        if key not in daily_group:
            daily_group[key]={
                "Sessions":0,
                "Minutes":0
            }


        daily_group[key][
            "Sessions"
        ]+=1


        daily_group[key][
            "Minutes"
        ]+=session[
            "Minutes"
        ]


    rows=[
        {
            "Date":(
                key.strftime(
                    "%d-%m-%Y"
                )
                if key
                else "-"
            ),
            "Sessions":value[
                "Sessions"
            ],
            "Study Time":duration_text(
                value[
                    "Minutes"
                ]
            )
        }
        for key,value in sorted(
            daily_group.items(),
            key=lambda item:
            item[0] or date.min,
            reverse=True
        )
    ]


    if rows:
        st.dataframe(
            pd.DataFrame(
                rows
            ),
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info(
            "No overall study history available."
        )


def profile_page():
    col1,col2=st.columns(
        [1,2],
        border=True,
        gap="small"
    )


    with col1:
        st.subheader(
            "Profile"
        )


        option=st.radio(
            "Select Option",
            [
                "My Profile",
                "Today's Study Time",
                "Overall Study Time"
            ],
            label_visibility="collapsed"
        )


    with col2:
        if option=="My Profile":
            my_profile()

        elif option=="Today's Study Time":
            today_study_time()

        else:
            overall_study_time()


def save_progress_page():
    student=st.session_state.student


    start=(
        st.session_state.overall_progress_start_time
        or
        st.session_state.logged_in_time
    )


    st.header(
        "Save Progress"
    )


    if not start:
        st.warning(
            "Overall progress start time is unavailable."
        )
        return


    current=now()


    c1,c2,c3=st.columns(
        3
    )


    c1.metric(
        "Session Started",
        start.strftime(
            "%I:%M:%S %p"
        )
    )


    c2.metric(
        "Current Time",
        current.strftime(
            "%I:%M:%S %p"
        )
    )


    c3.metric(
        "Unsaved Study Time",
        duration_text(
            elapsed_minutes(
                start,
                current
            )
        )
    )


    with st.form(
        "save_overall_progress_form"
    ):
        confirm=st.checkbox(
            "Confirm save overall study progress"
        )


        save=st.form_submit_button(
            "Save Progress",
            type="primary",
            use_container_width=True
        )


    if save:
        if not confirm:
            st.warning(
                "Confirm before saving progress."
            )
            return


        end=now()


        try:
            result=Database.save_overall_progress(
                st.session_state.department,
                student,
                start,
                end
            )


            st.session_state.overall_progress_start_time=end


            st.success(
                f"Overall progress saved successfully: "
                f"{duration_text(result['seconds']/60)}"
            )


        except Exception as error:
            st.error(
                f"Unable to save overall progress: {error}"
            )


def save_subject_progress_page():
    subject=st.session_state.selected_subject

    student=st.session_state.student

    start=st.session_state.selected_subject_start_time


    st.header(
        "Save Subject Progress"
    )


    if not subject or not start:
        st.info(
            "Select a subject first."
        )
        return


    course=Database.subject_details(
        st.session_state.department,
        st.session_state.batch,
        st.session_state.semester,
        subject,
        st.session_state.section
    ) or {}


    current=now()


    c1,c2,c3=st.columns(
        3
    )


    c1.metric(
        "Subject",
        subject
    )


    c2.metric(
        "Started",
        start.strftime(
            "%I:%M:%S %p"
        )
    )


    c3.metric(
        "Unsaved Time",
        duration_text(
            elapsed_minutes(
                start,
                current
            )
        )
    )


    st.write(
        f"**Semester:** "
        f"{st.session_state.semester} | "
        f"**Section:** "
        f"{st.session_state.section} | "
        f"**Type:** "
        f"{course.get('subject_type','Theory')} | "
        f"**Credits:** "
        f"{course.get('subject_credits',0)}"
    )


    with st.form(
        "save_subject_progress_form"
    ):
        confirm=st.checkbox(
            "Confirm save subject progress"
        )


        save=st.form_submit_button(
            "Save Subject Progress",
            type="primary",
            use_container_width=True
        )


    if save:
        if not confirm:
            st.warning(
                "Confirm before saving progress."
            )
            return


        end=now()


        try:
            result=Database.save_subject_progress(
                st.session_state.department,
                student,
                st.session_state.semester,
                subject,
                start,
                end
            )


            st.session_state.selected_subject_end_time=end

            st.session_state.selected_subject=None

            st.session_state.selected_subject_start_time=None

            st.session_state.subject_selector_version+=1


            st.session_state.flash_message=(
                f"{subject} progress saved successfully: "
                f"{duration_text(result['seconds']/60)}"
            )


            st.rerun()


        except Exception as error:
            st.error(
                f"Unable to save subject progress: {error}"
            )


def dashboard():
    department=st.session_state.department

    batch=st.session_state.batch

    section=st.session_state.section

    roll=st.session_state.roll_number


    latest_student=Database.student(
        department,
        batch,
        section,
        roll
    )


    if not latest_student:
        st.error(
            "Student account is no longer available for the selected batch and section."
        )
        return


    semester=Database.student_semester(
        department,
        batch,
        section,
        roll
    )


    if semester is None:
        st.error(
            "Semister is missing or invalid in your MongoDB student document."
        )

        st.code(
            f"Roll Number: {roll}\n"
            f"Expected field: semister"
        )

        return


    if st.session_state.semester!=semester:
        st.session_state.semester=semester

        st.session_state.selected_subject=None

        st.session_state.selected_subject_start_time=None

        st.session_state.selected_subject_end_time=None

        st.session_state.subject_selector_version+=1


    st.session_state.student=latest_student


    name=latest_student.get(
        "student_name",
        "Student"
    )


    locked=bool(
        st.session_state.selected_subject
    )


    with st.sidebar:
        st.header(
            "Student Portal"
        )


        st.write(
            f"**{name}**"
        )


        st.caption(
            f"{roll} | {department} | {batch}"
        )


        st.write(
            f"**Section {section}**"
        )


        st.write(
            f"**Semester {semester}**"
        )


        try:
            subjects=Database.theory_subjects(
                department,
                batch,
                semester,
                section
            )

        except Exception as error:
            subjects=[]

            st.error(
                f"Unable to load subjects: {error}"
            )


        if locked:
            st.selectbox(
                "Select Subject",
                [
                    st.session_state.selected_subject
                ],
                disabled=True,
                key="locked_subject"
            )


            st.caption(
                "Save Subject Progress to select another subject."
            )


        elif subjects:
            subject=st.selectbox(
                "Select Subject",
                subjects,
                index=None,
                placeholder="Select subject",
                key=(
                    f"subject_"
                    f"{semester}_"
                    f"{section}_"
                    f"{st.session_state.subject_selector_version}"
                )
            )


            if subject:
                st.session_state.selected_subject=subject

                st.session_state.selected_subject_start_time=now()

                st.session_state.selected_subject_end_time=None

                st.rerun()


        else:
            st.selectbox(
                "Select Subject",
                [
                    "No Theory Subjects Available"
                ],
                disabled=True
            )


        menu=option_menu(
            None,
            [
                "Learn",
                "Study",
                "Tasks",
                "View Profile",
                "Save Progress",
                "Save Subject Progress"
            ],
            icons=[
                "book",
                "file-earmark-pdf",
                "clipboard-check",
                "person",
                "save",
                "clock"
            ],
            default_index=0
        )


        if st.button(
            "Logout",
            use_container_width=True
        ):
            logout()


    st.title(
        "Students Tracking System"
    )


    st.write(
        f"Welcome **{name}**"
    )


    st.caption(
        f"Department: {department} | "
        f"Batch: {batch} | "
        f"Section: {section} | "
        f"Semester: {semester}"
    )


    if st.session_state.flash_message:
        st.success(
            st.session_state.flash_message
        )

        st.session_state.flash_message=None


    if st.session_state.selected_subject:
        st.success(
            f"Selected Subject: "
            f"{st.session_state.selected_subject} "
            f"| Section {section}"
        )

    else:
        st.info(
            f"Select a Semester {semester} "
            f"Theory subject for Section {section}."
        )


    if menu=="Learn":
        learn_page()


    elif menu=="Study":
        study_page()


    elif menu=="Tasks":
        tasks_page()


    elif menu=="View Profile":
        profile_page()


    elif menu=="Save Progress":
        save_progress_page()


    elif menu=="Save Subject Progress":
        save_subject_progress_page()


initialize_session()


if st.session_state.logged_in:
    dashboard()

else:
    st.title(
        "Students Tracking System"
    )

    st.write(
        "Login to access your learning portal."
    )

    alert_dialog()