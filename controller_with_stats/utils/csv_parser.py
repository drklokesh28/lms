import pandas as pd
from utils.list_parser import ListParser

class CSVParser:
    @staticmethod
    def read(file):
        return pd.read_csv(file)

    @staticmethod
    def clean_columns(dataframe):
        dataframe=dataframe.copy()
        dataframe.columns=[str(column).strip().lower().replace(" ","_") for column in dataframe.columns]
        return dataframe

    @staticmethod
    def clean_values(dataframe):
        dataframe=dataframe.copy()
        dataframe=dataframe.dropna(how="all")
        dataframe=dataframe.fillna("")
        return dataframe

    @classmethod
    def prepare(cls,dataframe):
        dataframe=cls.clean_columns(dataframe)
        dataframe=cls.clean_values(dataframe)
        return dataframe

    @classmethod
    def parse_students(cls,dataframe,batch=None):
        dataframe=cls.prepare(dataframe)

        dataframe=dataframe.rename(columns={
            "roll_number":"student_roll_number",
            "gender":"student_gender",
            "batch":"student_batch",
            "section":"student_section",
            "password":"student_password",
            "semester":"semister"
        })

        required=[
            "student_name",
            "student_roll_number",
            "student_gender",
            "student_section",
            "semister"
        ]

        missing=[column for column in required if column not in dataframe.columns]

        if missing:
            raise ValueError(f"Students CSV missing column(s): {', '.join(missing)}")

        if batch is not None:
            dataframe["student_batch"]=str(batch).strip()

        if "student_batch" not in dataframe.columns:
            raise ValueError("Batch is missing")

        dataframe["semister"]=pd.to_numeric(
            dataframe["semister"],
            errors="raise"
        ).astype(int)

        if not dataframe["semister"].between(1,8).all():
            raise ValueError("Semister must be between 1 and 8")

        if "student_password" not in dataframe.columns:
            dataframe["student_password"]=dataframe["student_roll_number"]

        dataframe["student_password"]=dataframe["student_password"].where(
            dataframe["student_password"].astype(str).str.strip()!="",
            dataframe["student_roll_number"]
        )

        text_columns=[
            "student_name",
            "student_roll_number",
            "student_batch",
            "student_gender",
            "student_section",
            "student_password"
        ]

        for column in text_columns:
            dataframe[column]=dataframe[column].astype(str).str.strip()

        dataframe=dataframe[
            (dataframe["student_name"]!="") &
            (dataframe["student_roll_number"]!="") &
            (dataframe["student_gender"]!="") &
            (dataframe["student_section"]!="")
        ]

        dataframe=dataframe.drop_duplicates(
            subset=["student_roll_number","student_batch"],
            keep="last"
        )

        return dataframe[
            [
                "student_name",
                "student_roll_number",
                "student_batch",
                "semister",
                "student_gender",
                "student_section",
                "student_password"
            ]
        ]

    @classmethod
    def parse_courses(cls,dataframe,batch):
        dataframe=cls.prepare(dataframe)

        dataframe=dataframe.rename(columns={
            "semister":"semester",
            "alloted_faculty_ids":"allotted_faculty_ids",
            "alloted_sections":"allotted_sections"
        })

        required=[
            "semester",
            "subject_name",
            "subject_credits",
            "subject_type",
            "allotted_faculty_ids",
            "allotted_sections"
        ]

        missing=[column for column in required if column not in dataframe.columns]

        if missing:
            raise ValueError(f"Subjects CSV missing column(s): {', '.join(missing)}")

        dataframe["batch"]=str(batch).strip()

        dataframe["semester"]=pd.to_numeric(
            dataframe["semester"],
            errors="raise"
        ).astype(int)

        dataframe["subject_credits"]=pd.to_numeric(
            dataframe["subject_credits"],
            errors="raise"
        )

        dataframe["allotted_faculty_ids"]=dataframe["allotted_faculty_ids"].apply(
            ListParser.parse_integer_list
        )

        dataframe["allotted_sections"]=dataframe["allotted_sections"].apply(
            ListParser.parse_string_list
        )

        dataframe=dataframe.drop_duplicates(
            subset=["batch","semester","subject_name"],
            keep="last"
        )

        return dataframe[
            [
                "batch",
                "semester",
                "subject_name",
                "subject_credits",
                "subject_type",
                "allotted_faculty_ids",
                "allotted_sections"
            ]
        ]

    @classmethod
    def parse_curriculum(cls,dataframe):
        dataframe=cls.prepare(dataframe)

        required=[
            "unit_number",
            "topic_name",
            "yt_url",
            "description"
        ]

        missing=[column for column in required if column not in dataframe.columns]

        if missing:
            raise ValueError(f"Curriculum CSV missing column(s): {', '.join(missing)}")

        dataframe["unit_number"]=pd.to_numeric(
            dataframe["unit_number"],
            errors="raise"
        ).astype(int)

        if not dataframe["unit_number"].between(1,5).all():
            raise ValueError("Unit number must be between 1 and 5")

        dataframe=dataframe.drop_duplicates(
            subset=["unit_number","topic_name"],
            keep="last"
        )

        return dataframe[
            [
                "unit_number",
                "topic_name",
                "yt_url",
                "description"
            ]
        ]

    @classmethod
    def parse_tasks(cls,dataframe):
        dataframe=cls.prepare(dataframe)

        required=[
            "question_name",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "marks"
        ]

        missing=[column for column in required if column not in dataframe.columns]

        if missing:
            raise ValueError(f"Tasks CSV missing column(s): {', '.join(missing)}")

        dataframe["correct_option"]=dataframe["correct_option"].astype(str).str.strip().str.upper()

        dataframe["marks"]=pd.to_numeric(
            dataframe["marks"],
            errors="raise"
        )

        dataframe=dataframe.drop_duplicates(
            subset=["question_name"],
            keep="last"
        )

        return dataframe[
            [
                "question_name",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_option",
                "marks"
            ]
        ]