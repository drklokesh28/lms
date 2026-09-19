from models.course import Course
from repositories.course_repository import CourseRepository
from database.index_manager import IndexManager
from utils.csv_parser import CSVParser
from utils.validators import Validator

class CourseService:
    def __init__(self,department):
        self.department=department
        self.repository=CourseRepository(department)
        IndexManager.create_course_indexes(department)

    def import_courses(self,dataframe,batch):
        dataframe=CSVParser.parse_courses(dataframe,batch)
        courses=[]
        invalid_rows=0
        existing=0
        changed=0
        new=0
        for record in dataframe.to_dict("records"):
            if not Validator.validate_course(record):
                invalid_rows+=1
                continue
            current=self.repository.get_course(record["batch"],record["semester"],record["subject_name"])
            if current is None:
                new+=1
            elif self._is_changed(current,record):
                changed+=1
            else:
                existing+=1
            courses.append(Course.from_dict(record))
        result=self.repository.bulk_upsert(courses)
        return {"uploaded":len(dataframe),"valid":len(courses),"invalid":invalid_rows,"already_existing":existing,"inserted":result.upserted_count if result else 0,"updated":result.modified_count if result else 0,"total":self.repository.count({"batch":batch})}

    def get_courses(self,batch=None):
        return self.repository.get_by_batch(batch) if batch else self.repository.find()

    def get_courses_by_semester(self,batch,semester):
        return self.repository.get_by_semester(batch,semester)

    def get_course(self,batch,semester,subject_name):
        return self.repository.get_course(batch,semester,subject_name)

    def get_batches(self):
        return self.repository.get_batches()

    def get_semesters(self,batch):
        return self.repository.get_semesters(batch)

    def get_subjects(self,batch,semester):
        return self.repository.get_subjects(batch,semester)

    def update_course(self,batch,semester,subject_name,data):
        course=Course.from_dict(data)
        if not course.validate():
            raise ValueError("Faculty IDs and sections count must match")
        return self.repository.update_course(batch,semester,subject_name,course.to_dict())

    def delete_course(self,batch,semester,subject_name):
        return self.repository.delete_course(batch,semester,subject_name)

    @staticmethod
    def _is_changed(current,new):
        fields=["batch","semester","subject_name","subject_credits","subject_type","allotted_faculty_ids","allotted_sections"]
        return any(current.get(field)!=new.get(field) for field in fields)

    def delete_by_ids(self,ids):
        return self.repository.delete_by_ids(ids)

    def update_subject(self,batch,semester,subject_name,subject_credits,subject_type,allotted_faculty_ids,allotted_sections):
        document={
            "subject_credits":float(subject_credits),
            "subject_type":str(subject_type).strip(),
            "allotted_faculty_ids":[int(value) for value in allotted_faculty_ids],
            "allotted_sections":[str(value).strip() for value in allotted_sections]
        }

        return self.repository.update_one(
            {
                "batch":batch,
                "semester":int(semester),
                "subject_name":subject_name
            },
            {
                "$set":document
            }
        )