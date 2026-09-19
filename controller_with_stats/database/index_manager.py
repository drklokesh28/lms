from pymongo import ASCENDING
from config import Config
from database.mongo_client import MongoManager

class IndexManager:
    @classmethod
    def create_student_indexes(cls,department):
        collection=MongoManager.get_collection(department,Config.STUDENTS_COLLECTION)
        indexes=collection.index_information()

        if "unique_batch_students" in indexes:
            collection.drop_index("unique_batch_students")

        if "student_roll_lookup" in indexes:
            collection.drop_index("student_roll_lookup")

        if "student_section_lookup" in indexes:
            collection.drop_index("student_section_lookup")

        collection.create_index(
            [
                ("student_roll_number",ASCENDING),
                ("student_batch",ASCENDING)
            ],
            unique=True,
            name="unique_student"
        )

        collection.create_index(
            [
                ("student_batch",ASCENDING),
                ("student_section",ASCENDING)
            ],
            name="student_batch_section"
        )

        collection.create_index(
            [
                ("student_batch",ASCENDING),
                ("semister",ASCENDING)
            ],
            name="student_batch_semister"
        )

    @classmethod
    def create_course_indexes(cls,department):
        collection=MongoManager.get_collection(department,Config.COURSES_COLLECTION)

        collection.create_index(
            [
                ("batch",ASCENDING),
                ("semester",ASCENDING),
                ("subject_name",ASCENDING)
            ],
            unique=True,
            name="unique_course"
        )

    @classmethod
    def create_material_indexes(cls,department):
        collection=MongoManager.get_collection(department,Config.MATERIALS_COLLECTION)

        collection.create_index(
            [
                ("batch",ASCENDING),
                ("semester",ASCENDING),
                ("subject_name",ASCENDING),
                ("faculty_id",ASCENDING)
            ],
            unique=True,
            name="unique_material"
        )

    @classmethod
    def create_curriculum_indexes(cls,department):
        collection=MongoManager.get_collection(department,Config.CURRICULUM_COLLECTION)

        collection.create_index(
            [
                ("batch",ASCENDING),
                ("semester",ASCENDING),
                ("subject_name",ASCENDING),
                ("faculty_id",ASCENDING)
            ],
            unique=True,
            name="unique_curriculum"
        )

    @classmethod
    def create_task_indexes(cls,department,collection_name):
        collection=MongoManager.get_assignment_collection(department,collection_name)

        collection.create_index(
            [
                ("batch",ASCENDING),
                ("task_name",ASCENDING),
                ("task_uploaded_date",ASCENDING)
            ],
            unique=True,
            name="unique_task"
        )

    @classmethod
    def create_department_indexes(cls,department):
        cls.create_student_indexes(department)
        cls.create_course_indexes(department)
        cls.create_material_indexes(department)
        cls.create_curriculum_indexes(department)