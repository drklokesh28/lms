from config import Config
from utils.list_parser import ListParser

class Validator:
    @staticmethod
    def required_columns(dataframe,columns):
        missing=[column for column in columns if column not in dataframe.columns]
        return len(missing)==0,missing

    @staticmethod
    def validate_student(data):
        required=[
            "student_name",
            "student_roll_number",
            "student_gender",
            "student_batch",
            "student_section",
            "student_password",
            "semister"
        ]

        if not all(str(data.get(field,"")).strip() for field in required):
            return False

        try:
            semister=int(data["semister"])
        except:
            return False

        return 1<=semister<=8

    @staticmethod
    def validate_course(data):
        required=[
            "batch",
            "semester",
            "subject_name",
            "subject_credits",
            "subject_type",
            "allotted_faculty_ids",
            "allotted_sections"
        ]

        if not all(field in data for field in required):
            return False

        if data["subject_type"] not in Config.SUBJECT_TYPES:
            return False

        return ListParser.validate_pair_lengths(
            data["allotted_faculty_ids"],
            data["allotted_sections"]
        )

    @staticmethod
    def validate_material(data):
        required=[
            "batch",
            "semester",
            "subject_name",
            "subject_type",
            "faculty_id",
            "materials",
            "sections"
        ]

        if not all(field in data for field in required):
            return False

        return bool(data["materials"]) and bool(data["sections"])

    @staticmethod
    def validate_curriculum(data):
        required=[
            "batch",
            "semester",
            "subject_name",
            "subject_type",
            "faculty_id",
            "sections"
        ]

        if not all(field in data for field in required):
            return False

        return bool(data["sections"])

    @staticmethod
    def validate_question(data):
        required=[
            "question_name",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "marks"
        ]

        if not all(str(data.get(field,"")).strip() for field in required):
            return False

        return str(data["correct_option"]).strip().upper() in ["A","B","C","D"] and float(data["marks"])>0

    @staticmethod
    def validate_task(data):
        required=[
            "task_name",
            "task_uploaded_date",
            "batch",
            "semester",
            "subject_name",
            "subject_type",
            "faculty_id",
            "sections",
            "questions"
        ]

        if not all(field in data for field in required):
            return False

        return bool(data["sections"]) and bool(data["questions"])