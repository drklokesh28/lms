from pymongo import UpdateOne
from config import Config
from database.mongo_client import MongoManager
from repositories.base_repository import BaseRepository

class CourseRepository(BaseRepository):
    def __init__(self,department):
        super().__init__(MongoManager.get_collection(department,Config.COURSES_COLLECTION))

    def get_by_batch(self,batch):
        return self.find({"batch":batch})

    def get_by_semester(self,batch,semester):
        return self.find({"batch":batch,"semester":int(semester)})

    def get_course(self,batch,semester,subject_name):
        return self.find_one({"batch":batch,"semester":int(semester),"subject_name":subject_name})

    def get_by_faculty(self,faculty_id):
        return self.find({"allotted_faculty_ids":int(faculty_id)})

    def get_by_faculty_batch(self,faculty_id,batch):
        return self.find({"batch":batch,"allotted_faculty_ids":int(faculty_id)})

    def bulk_upsert(self,courses):
        operations=[]
        for course in courses:
            data=course.to_dict() if hasattr(course,"to_dict") else course
            query={"batch":data["batch"],"semester":data["semester"],"subject_name":data["subject_name"]}
            operations.append(UpdateOne(query,{"$set":data},upsert=True))
        return self.bulk_write(operations) if operations else None

    def update_course(self,batch,semester,subject_name,data):
        query={"batch":batch,"semester":int(semester),"subject_name":subject_name}
        return self.update_one(query,{"$set":data})

    def delete_course(self,batch,semester,subject_name):
        return self.delete_one({"batch":batch,"semester":int(semester),"subject_name":subject_name})

    def get_batches(self):
        return sorted(self.distinct("batch"))

    def get_semesters(self,batch):
        return sorted(self.distinct("semester",{"batch":batch}))

    def get_subjects(self,batch,semester):
        return sorted(self.distinct("subject_name",{"batch":batch,"semester":int(semester)}))

    def get_subject_types(self,batch,semester):
        return sorted(self.distinct("subject_type",{"batch":batch,"semester":int(semester)}))
    def update_subject(self,batch,semester,subject_name,subject_credits,subject_type,allotted_faculty_ids,allotted_sections):
        return self.repository.update_subject(
            batch,
            semester,
            subject_name,
            {
                "subject_credits":float(subject_credits),
                "subject_type":subject_type,
                "allotted_faculty_ids":[int(value) for value in allotted_faculty_ids],
                "allotted_sections":allotted_sections
            }
        )