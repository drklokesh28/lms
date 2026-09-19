import os
import re
import streamlit as st

from bson import ObjectId
from pymongo import MongoClient

from config import Config


class Database:

    @staticmethod
    @st.cache_resource
    def client():

        uri=os.getenv("MONGODB_URI")

        if not uri:

            try:
                uri=st.secrets["DataBase"]["client"]

            except Exception:
                uri="mongodb://localhost:27017"

        client=MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        client.admin.command("ping")

        return client


    @classmethod
    def test(cls):
        return cls.client().admin.command("ping")


    @classmethod
    def db(cls,department):
        return cls.client()[str(department).strip()]


    @classmethod
    def students(cls,department):
        return cls.db(department)[Config.STUDENTS_COLLECTION]


    @classmethod
    def courses(cls,department):
        return cls.db(department)[Config.COURSES_COLLECTION]


    @classmethod
    def curriculums(cls,department):
        return cls.db(department)[Config.CURRICULUM_COLLECTION]


    @classmethod
    def materials(cls,department):
        return cls.db(department)[Config.MATERIALS_COLLECTION]


    @classmethod
    def assignment_db(cls,department):
        return cls.client()[
            f"{str(department).strip()}{Config.ASSIGNMENTS_SUFFIX}"
        ]


    @classmethod
    def activity_db(cls,department):
        return cls.client()[
            f"{str(department).strip()}_students_activity_logs"
        ]


    @classmethod
    def activity_logs(cls,department):
        return cls.activity_db(department)["activity_logs"]


    @classmethod
    def daily_activity_logs(cls,department):
        return cls.activity_db(department)["daily_activity_logs"]


    @staticmethod
    def _text(value):
        return str(value).strip() if value is not None else ""


    @staticmethod
    def _semester(value):

        try:
            value=int(value)

            if 1<=value<=8:
                return value

        except:
            pass

        return None


    # ============================================================
    # STUDENTS
    # ============================================================

    @classmethod
    def student_batches(cls,department):

        values=cls.students(department).distinct(
            "student_batch",
            {
                "student_batch":{
                    "$exists":True,
                    "$nin":[None,""]
                }
            }
        )

        return sorted({
            cls._text(value)
            for value in values
            if cls._text(value)
        })


    @classmethod
    def batch_semester(cls,department,batch):

        values=cls.students(department).distinct(
            "semister",
            {
                "student_batch":cls._text(batch),
                "semister":{
                    "$exists":True
                }
            }
        )

        semesters=sorted({
            semester
            for semester in (
                cls._semester(value)
                for value in values
            )
            if semester is not None
        })

        if len(semesters)==1:
            return semesters[0]

        return None


    @classmethod
    def sections(cls,department,batch):

        values=cls.students(department).distinct(
            "student_section",
            {
                "student_batch":cls._text(batch)
            }
        )

        return sorted({
            cls._text(value)
            for value in values
            if cls._text(value)
        })


    @classmethod
    def students_by_section(cls,department,batch,section):

        return list(
            cls.students(department).find(
                {
                    "student_batch":cls._text(batch),
                    "student_section":cls._text(section)
                }
            ).sort(
                "student_roll_number",
                1
            )
        )


    @classmethod
    def student(cls,department,batch,section,roll):

        return cls.students(department).find_one({
            "student_batch":cls._text(batch),
            "student_section":cls._text(section),
            "student_roll_number":cls._text(roll)
        })


    @classmethod
    def student_semester(
        cls,
        department,
        batch,
        section,
        roll
    ):

        student=cls.student(
            department,
            batch,
            section,
            roll
        )

        if not student:
            return None

        return cls._semester(
            student.get("semister")
        )


    @classmethod
    def change_password(
        cls,
        department,
        batch,
        section,
        roll,
        password
    ):

        return cls.students(department).update_one(
            {
                "student_batch":cls._text(batch),
                "student_section":cls._text(section),
                "student_roll_number":cls._text(roll)
            },
            {
                "$set":{
                    "student_password":str(password)
                }
            }
        )


    # ============================================================
    # COURSES
    # ============================================================

    @staticmethod
    def _course_semester(course):

        try:
            return int(
                course.get(
                    "semester",
                    course.get("semister")
                )
            )

        except:
            return None


    @staticmethod
    def _course_faculty_ids(course):

        values=course.get(
            "allotted_faculty_ids",
            course.get(
                "alloted_faculty_ids",
                []
            )
        )

        if isinstance(values,(str,int)):
            values=[values]

        return list(values or [])


    @staticmethod
    def _course_sections(course):

        values=course.get(
            "allotted_sections",
            course.get(
                "alloted_sections",
                []
            )
        )

        if isinstance(values,str):

            values=[
                value.strip()
                for value in values.split(",")
                if value.strip()
            ]

        return [
            str(value).strip()
            for value in (values or [])
            if str(value).strip()
        ]


    @classmethod
    def _faculty_for_section(
        cls,
        course,
        section
    ):

        section=cls._text(section)

        faculty_ids=cls._course_faculty_ids(
            course
        )

        sections=cls._course_sections(
            course
        )

        for faculty_id,current_section in zip(
            faculty_ids,
            sections
        ):

            if cls._text(current_section)==section:

                try:
                    return int(faculty_id)

                except:
                    return None

        return None


    @classmethod
    def theory_subjects(
        cls,
        department,
        batch,
        semester,
        section
    ):

        subjects=[]

        courses=cls.courses(
            department
        ).find({
            "batch":cls._text(batch)
        })

        for course in courses:

            if cls._course_semester(course)!=int(semester):
                continue

            if cls._text(
                course.get("subject_type")
            ).lower()!="theory":
                continue

            faculty_id=cls._faculty_for_section(
                course,
                section
            )

            if faculty_id is None:
                continue

            subject=cls._text(
                course.get("subject_name")
            )

            if subject:
                subjects.append(subject)

        return sorted(
            set(subjects)
        )


    @classmethod
    def subject_details(
        cls,
        department,
        batch,
        semester,
        subject,
        section
    ):

        courses=cls.courses(
            department
        ).find({
            "batch":cls._text(batch),
            "subject_name":cls._text(subject)
        })

        for course in courses:

            if cls._course_semester(course)!=int(semester):
                continue

            faculty_id=cls._faculty_for_section(
                course,
                section
            )

            if faculty_id is None:
                continue

            result=dict(course)

            result["faculty_id"]=faculty_id
            result["student_section"]=cls._text(section)

            return result

        return None


    # ============================================================
    # CURRICULUM
    # ============================================================

    @classmethod
    def curriculum(
        cls,
        department,
        batch,
        semester,
        subject,
        section
    ):

        course=cls.subject_details(
            department,
            batch,
            semester,
            subject,
            section
        )

        if not course:
            return None

        faculty_id=course["faculty_id"]

        return cls.curriculums(
            department
        ).find_one({
            "batch":cls._text(batch),
            "semester":int(semester),
            "subject_name":cls._text(subject),
            "faculty_id":{
                "$in":[
                    faculty_id,
                    str(faculty_id)
                ]
            },
            "sections":cls._text(section)
        })


    # ============================================================
    # MATERIALS
    # ============================================================

    @classmethod
    def subject_materials(
        cls,
        department,
        batch,
        semester,
        subject,
        section
    ):

        course=cls.subject_details(
            department,
            batch,
            semester,
            subject,
            section
        )

        if not course:
            return None

        faculty_id=course["faculty_id"]

        return cls.materials(
            department
        ).find_one({
            "batch":cls._text(batch),
            "semester":int(semester),
            "subject_name":cls._text(subject),
            "faculty_id":{
                "$in":[
                    faculty_id,
                    str(faculty_id)
                ]
            },
            "sections":cls._text(section)
        })


    # ============================================================
    # TASKS
    # ============================================================

    @staticmethod
    def _normalize(value):

        value=str(value).strip().lower()

        value=re.sub(
            r"[^a-z0-9]+",
            "_",
            value
        )

        return value.strip("_")


    @classmethod
    def task_collection(
        cls,
        department,
        batch,
        semester,
        subject
    ):

        subject_name=cls._normalize(
            subject
        )

        batch_name=cls._normalize(
            batch
        )

        semester_name=cls._normalize(
            f"semester_{int(semester)}"
        )

        collection_name=(
            f"{subject_name}_"
            f"{batch_name}_"
            f"{semester_name}"
        )

        return cls.assignment_db(
            department
        )[collection_name]


    @classmethod
    def student_tasks(
        cls,
        department,
        batch,
        semester,
        subject,
        section,
        roll
    ):

        course=cls.subject_details(
            department,
            batch,
            semester,
            subject,
            section
        )

        if not course:
            return []

        faculty_id=course["faculty_id"]

        section=cls._text(section)
        roll=cls._text(roll)

        collection=cls.task_collection(
            department,
            batch,
            semester,
            subject
        )

        tasks=list(
            collection.find({
                "batch":cls._text(batch),
                "subject_name":cls._text(subject)
            }).sort([
                ("task_uploaded_date",-1),
                ("task_name",1)
            ])
        )

        result=[]

        for task in tasks:

            if cls._course_semester(task)!=int(semester):
                continue

            try:

                if int(
                    task.get("faculty_id")
                )!=int(faculty_id):

                    continue

            except:
                continue

            sections=task.get(
                "sections",
                []
            )

            if isinstance(sections,str):

                sections=[
                    value.strip()
                    for value in sections.split(",")
                    if value.strip()
                ]

            sections=[
                cls._text(value)
                for value in sections
            ]

            if section not in sections:
                continue

            has_student=any(
                cls._text(
                    track.get(
                        "student_roll_number"
                    )
                )==roll
                and
                cls._text(
                    track.get(
                        "student_section"
                    )
                )==section

                for track in task.get(
                    "track",
                    []
                )
            )

            if has_student:
                result.append(task)

        return result


    @classmethod
    def complete_task(
        cls,
        department,
        batch,
        semester,
        subject,
        section,
        task_id,
        roll,
        total,
        selected_answers,
        results
    ):

        try:

            if not isinstance(
                task_id,
                ObjectId
            ):

                task_id=ObjectId(
                    str(task_id)
                )

        except:
            raise ValueError(
                "Invalid task id"
            )

        section=cls._text(section)
        roll=cls._text(roll)

        collection=cls.task_collection(
            department,
            batch,
            semester,
            subject
        )

        return collection.update_one(
            {
                "_id":task_id,
                "track":{
                    "$elemMatch":{
                        "student_roll_number":roll,
                        "student_section":section
                    }
                }
            },
            {
                "$set":{
                    "track.$[student].student_status":"Completed",
                    "track.$[student].student_marks":float(total),
                    "track.$[student].selected_answers":selected_answers,
                    "track.$[student].question_results":results
                }
            },
            array_filters=[
                {
                    "student.student_roll_number":roll,
                    "student.student_section":section
                }
            ]
        )


    # ============================================================
    # ACTIVITY READ
    # ============================================================

    @classmethod
    def _activity_student(
        cls,
        collection,
        batch,
        section,
        roll
    ):

        batch=cls._text(batch)
        section=cls._text(section)
        roll=cls._text(roll)

        document=collection.find_one({
            "batch":batch,
            "students_list":{
                "$elemMatch":{
                    "student_roll_number":roll,
                    "student_section":section
                }
            }
        })

        if not document:
            return {}

        student=next(
            (
                student
                for student in document.get(
                    "students_list",
                    []
                )
                if cls._text(
                    student.get(
                        "student_roll_number"
                    )
                )==roll
                and cls._text(
                    student.get(
                        "student_section"
                    )
                )==section
            ),
            {}
        )

        if (
            student
            and
            "tracks" not in student
            and
            "tarcks" in student
        ):

            student=dict(student)

            student["tracks"]=student.get(
                "tarcks",
                []
            )

        return student


    @classmethod
    def student_subject_activity(
        cls,
        department,
        batch,
        section,
        roll
    ):

        student=cls._activity_student(
            cls.activity_logs(department),
            batch,
            section,
            roll
        )

        if student:
            return student

        return {
            "student_roll_number":cls._text(roll),
            "student_section":cls._text(section),
            "tracks":[]
        }


    @classmethod
    def student_daily_activity(
        cls,
        department,
        batch,
        section,
        roll
    ):

        student=cls._activity_student(
            cls.daily_activity_logs(
                department
            ),
            batch,
            section,
            roll
        )

        if student:
            return student

        return {
            "student_roll_number":cls._text(roll),
            "student_section":cls._text(section),
            "track":[]
        }


    # ============================================================
    # ACTIVITY WRITE
    # ============================================================

    @classmethod
    def _activity_doc_student(
        cls,
        collection,
        batch,
        student,
        field
    ):

        batch=cls._text(batch)

        roll=cls._text(
            student.get(
                "student_roll_number"
            )
        )

        section=cls._text(
            student.get(
                "student_section"
            )
        )

        document=collection.find_one({
            "batch":batch
        })

        if not document:

            document={
                "batch":batch,
                "students_list":[]
            }

        students=document.setdefault(
            "students_list",
            []
        )

        target=next(
            (
                current
                for current in students

                if cls._text(
                    current.get(
                        "student_roll_number"
                    )
                )==roll

                and cls._text(
                    current.get(
                        "student_section"
                    )
                )==section
            ),
            None
        )

        if target is None:

            target={
                "student_name":cls._text(
                    student.get(
                        "student_name"
                    )
                ),
                "student_roll_number":roll,
                "student_section":section,
                field:[]
            }

            students.append(target)

        target.setdefault(
            field,
            []
        )

        return document,target


    @staticmethod
    def _date_text(value):

        if hasattr(value,"strftime"):
            return value.strftime(
                "%Y-%m-%d"
            )

        return str(value)


    @staticmethod
    def _time_text(value):

        if hasattr(value,"strftime"):
            return value.strftime(
                "%H:%M:%S"
            )

        return str(value)


    @classmethod
    def save_subject_progress(
        cls,
        department,
        student,
        semester,
        subject,
        start,
        end
    ):

        seconds=max(
            0,
            int(
                (end-start).total_seconds()
            )
        )

        batch=cls._text(
            student.get(
                "student_batch"
            )
        )

        section=cls._text(
            student.get(
                "student_section"
            )
        )

        course=cls.subject_details(
            department,
            batch,
            semester,
            subject,
            section
        )

        if not course:

            raise ValueError(
                "Subject details could not be resolved for this section."
            )

        collection=cls.activity_logs(
            department
        )

        document,target=cls._activity_doc_student(
            collection,
            batch,
            student,
            "tracks"
        )

        subject_track=next(
            (
                track
                for track in target["tracks"]

                if cls._text(
                    track.get(
                        "subject_name"
                    )
                )==cls._text(subject)

                and cls._semester(
                    track.get(
                        "subject_semister",
                        track.get(
                            "subject_semester"
                        )
                    )
                )==int(semester)
            ),
            None
        )

        if subject_track is None:

            subject_track={
                "subject_name":cls._text(
                    subject
                ),
                "subject_semister":str(
                    int(semester)
                ),
                "subject_type":cls._text(
                    course.get(
                        "subject_type",
                        "Theory"
                    )
                ),
                "subject_credits":course.get(
                    "subject_credits",
                    0
                ),
                "track_subjects":[]
            }

            target["tracks"].append(
                subject_track
            )

        date_key=cls._date_text(
            start
        )

        daily=next(
            (
                day
                for day in subject_track[
                    "track_subjects"
                ]
                if cls._text(
                    day.get("date")
                )==date_key
            ),
            None
        )

        if daily is None:

            daily={
                "date":date_key,
                "sessions":[]
            }

            subject_track[
                "track_subjects"
            ].append(daily)

        sessions=daily.setdefault(
            "sessions",
            []
        )

        if isinstance(
            sessions,
            dict
        ):

            sessions=[sessions]

            daily["sessions"]=sessions

        sessions.append({
            "start_time":cls._time_text(start),
            "end_time":cls._time_text(end),
            "hours_spent":seconds//3600,
            "minutes_spent":round(
                seconds/60,
                2
            ),
            "duration_seconds":seconds
        })

        collection.replace_one(
            {
                "batch":batch
            },
            document,
            upsert=True
        )

        return {
            "seconds":seconds
        }


    @classmethod
    def save_overall_progress(
        cls,
        department,
        student,
        start,
        end
    ):

        seconds=max(
            0,
            int(
                (end-start).total_seconds()
            )
        )

        batch=cls._text(
            student.get(
                "student_batch"
            )
        )

        collection=cls.daily_activity_logs(
            department
        )

        document,target=cls._activity_doc_student(
            collection,
            batch,
            student,
            "track"
        )

        date_key=cls._date_text(
            start
        )

        daily=next(
            (
                day
                for day in target["track"]
                if cls._text(
                    day.get("date")
                )==date_key
            ),
            None
        )

        if daily is None:

            daily={
                "date":date_key,
                "sessions":[]
            }

            target["track"].append(
                daily
            )

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
            sessions=[sessions]

        daily.pop(
            "session",
            None
        )

        daily["sessions"]=sessions

        sessions.append({
            "start_time":cls._time_text(start),
            "end_time":cls._time_text(end),
            "hours_studied":seconds//3600,
            "minutes_spent":round(
                seconds/60,
                2
            ),
            "duration_seconds":seconds
        })

        collection.replace_one(
            {
                "batch":batch
            },
            document,
            upsert=True
        )

        return {
            "seconds":seconds
        }