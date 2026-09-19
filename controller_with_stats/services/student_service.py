from models.student import Student
from repositories.student_repository import StudentRepository
from database.index_manager import IndexManager
from utils.csv_parser import CSVParser
from utils.validators import Validator


class StudentService:

    def __init__(self,department):
        self.department=department
        self.repository=StudentRepository(department)
        IndexManager.create_student_indexes(department)

    def import_students(self,dataframe,batch):
        dataframe=CSVParser.parse_students(
            dataframe,
            batch
        )

        current_rows=self.repository.get_by_batch(batch)

        current={
            str(row.get("student_roll_number","")).strip():row
            for row in current_rows
        }

        students=[]

        invalid=0
        existing=0
        updated=0
        inserted=0

        for record in dataframe.to_dict("records"):

            if not Validator.validate_student(record):
                invalid+=1
                continue

            student=Student.from_dict(record)

            old=current.get(
                student.student_roll_number
            )

            if old is None:
                inserted+=1

            elif self._is_changed(
                old,
                student.to_dict()
            ):
                updated+=1

            else:
                existing+=1

            students.append(student)

        result=None

        if students:
            result=self.repository.upsert_students(
                students
            )

        semisters=sorted(
            set(
                student.semister
                for student in students
            )
        )

        return {
            "uploaded":len(dataframe),
            "valid":len(students),
            "invalid":invalid,
            "already_existing":existing,
            "inserted":inserted,
            "updated":updated,
            "total":self.repository.count_by_batch(batch),
            "semister":semisters[0] if len(semisters)==1 else None
        }

    def replace_students(self,batch,dataframe):
        dataframe=dataframe.copy()

        if dataframe.empty:
            raise ValueError(
                "Student dataframe cannot be empty"
            )

        required=[
            "student_name",
            "student_roll_number",
            "student_gender",
            "student_section",
            "student_password",
            "semister"
        ]

        missing=[
            column
            for column in required
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing fields: {', '.join(missing)}"
            )

        dataframe["semister"]=dataframe["semister"].astype(int)

        if not dataframe["semister"].between(1,8).all():
            raise ValueError(
                "Semister must be between 1 and 8"
            )

        rolls=dataframe[
            "student_roll_number"
        ].astype(str).str.strip()

        if rolls.duplicated().any():
            raise ValueError(
                "Duplicate roll numbers are not allowed"
            )

        existing=self.repository.get_by_batch(
            batch
        )

        existing_rolls={
            str(student.get("student_roll_number","")).strip()
            for student in existing
        }

        new_rolls=set()

        for record in dataframe.to_dict("records"):
            record=dict(record)

            record["student_batch"]=str(batch).strip()

            record["student_roll_number"]=str(
                record["student_roll_number"]
            ).strip()

            if not str(
                record.get("student_password","")
            ).strip():

                record["student_password"]=record[
                    "student_roll_number"
                ]

            if not Validator.validate_student(record):
                raise ValueError(
                    f"Invalid student: {record['student_roll_number']}"
                )

            student=Student.from_dict(record)

            new_rolls.add(
                student.student_roll_number
            )

            old=self.repository.get_by_roll_number(
                student.student_roll_number,
                batch
            )

            if old:
                self.repository.update_student(
                    student.student_roll_number,
                    batch,
                    student.to_dict()
                )
            else:
                self.repository.upsert_students(
                    [student]
                )

        removed=existing_rolls-new_rolls

        for roll_number in removed:
            self.repository.delete_student(
                roll_number,
                batch
            )

        return True

    def get_students(self,batch):
        return self.repository.get_by_batch(
            batch
        )

    def get_students_by_section(self,batch,section):
        return self.repository.get_by_batch_section(
            batch,
            section
        )

    def get_student(self,roll_number,batch=None):
        return self.repository.get_by_roll_number(
            roll_number,
            batch
        )

    def get_batches(self):
        return self.repository.get_batches()

    def get_sections(self,batch):
        return self.repository.get_sections(
            batch
        )

    def get_semisters(self,batch):
        return self.repository.get_semisters(
            batch
        )

    def get_semister(self,batch):
        return self.repository.get_semister(
            batch
        )

    def update_semister(self,batch,semister):
        semister=int(semister)

        if not 1<=semister<=8:
            raise ValueError(
                "Semister must be between 1 and 8"
            )

        return self.repository.update_semister(
            batch,
            semister
        )

    def update_student(self,old_roll_number,batch,data):
        data=dict(data)

        data["student_batch"]=str(batch).strip()
        data["student_roll_number"]=str(
            data["student_roll_number"]
        ).strip()

        data["semister"]=int(
            data["semister"]
        )

        if not str(
            data.get("student_password","")
        ).strip():

            data["student_password"]=data[
                "student_roll_number"
            ]

        if not Validator.validate_student(data):
            raise ValueError(
                "Invalid student data"
            )

        student=Student.from_dict(data)

        return self.repository.update_student(
            old_roll_number,
            batch,
            student.to_dict()
        )

    def delete_student(self,roll_number,batch):
        return self.repository.delete_student(
            roll_number,
            batch
        )

    def delete_batch(self,batch):
        return self.repository.delete_batch(
            batch
        )

    def delete_by_ids(self,ids):
        return self.repository.delete_by_ids(
            ids
        )

    @staticmethod
    def _is_changed(current,new):
        fields=[
            "student_name",
            "student_roll_number",
            "student_batch",
            "semister",
            "student_gender",
            "student_section",
            "student_password"
        ]

        return any(
            str(current.get(field,"")) !=
            str(new.get(field,""))
            for field in fields
        )