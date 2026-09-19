from pymongo import UpdateOne
from config import Config
from database.mongo_client import MongoManager
from repositories.base_repository import BaseRepository

class MaterialRepository(BaseRepository):
    def __init__(self,department):
        super().__init__(MongoManager.get_collection(department,Config.MATERIALS_COLLECTION))

    def get_by_faculty(self,faculty_id):
        return self.find({"faculty_id":int(faculty_id)})

    def get_by_faculty_batch(self,faculty_id,batch):
        return self.find({"faculty_id":int(faculty_id),"batch":str(batch).strip()})

    def get_by_course(self,batch,semester,subject_name):
        return self.find({"batch":str(batch).strip(),"semester":int(semester),"subject_name":subject_name})

    def get_material(self,batch,semester,subject_name,faculty_id):
        return self.find_one({"batch":str(batch).strip(),"semester":int(semester),"subject_name":subject_name,"faculty_id":int(faculty_id)})

    def upsert_material(self,material):
        data=material.to_dict() if hasattr(material,"to_dict") else material
        query={"batch":data["batch"],"semester":int(data["semester"]),"subject_name":data["subject_name"],"faculty_id":int(data["faculty_id"])}
        return self.update_one(query,{"$set":data},upsert=True)

    def bulk_upsert(self,materials):
        operations=[]
        for material in materials:
            data=material.to_dict() if hasattr(material,"to_dict") else material
            query={"batch":data["batch"],"semester":int(data["semester"]),"subject_name":data["subject_name"],"faculty_id":int(data["faculty_id"])}
            operations.append(UpdateOne(query,{"$set":data},upsert=True))
        return self.bulk_write(operations) if operations else None

    def update_material(self,batch,semester,subject_name,faculty_id,data):
        return self.update_one({"batch":str(batch).strip(),"semester":int(semester),"subject_name":subject_name,"faculty_id":int(faculty_id)},{"$set":data})

    def delete_material(self,batch,semester,subject_name,faculty_id):
        return self.delete_one({"batch":str(batch).strip(),"semester":int(semester),"subject_name":subject_name,"faculty_id":int(faculty_id)})

    def get_batches(self):
        return sorted(self.distinct("batch"))

    def get_semesters(self,batch):
        return sorted(self.distinct("semester",{"batch":str(batch).strip()}))

    def get_subjects(self,batch,semester):
        return sorted(self.distinct("subject_name",{"batch":str(batch).strip(),"semester":int(semester)}))