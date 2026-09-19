from pymongo import UpdateOne
from database.mongo_client import MongoManager
from repositories.base_repository import BaseRepository
from bson import ObjectId

class TaskRepository(BaseRepository):
    def __init__(self,department,collection_name):
        self.department=department
        self.collection_name=collection_name
        super().__init__(MongoManager.get_assignment_collection(department,collection_name))

    def get_tasks(self,batch=None,faculty_id=None):
        query={}
        if batch:
            query["batch"]=batch
        if faculty_id is not None:
            query["faculty_id"]=int(faculty_id)
        return self.find(query)

    def get_task(self,task_name,task_uploaded_date,batch):
        return self.find_one({"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":batch})

    def upsert_task(self,task):
        data=task.to_dict() if hasattr(task,"to_dict") else task
        query={"task_name":data["task_name"],"task_uploaded_date":data["task_uploaded_date"],"batch":data["batch"]}
        return self.update_one(query,{"$set":data},upsert=True)

    def bulk_upsert(self,tasks):
        operations=[]
        for task in tasks:
            data=task.to_dict() if hasattr(task,"to_dict") else task
            query={"task_name":data["task_name"],"task_uploaded_date":data["task_uploaded_date"],"batch":data["batch"]}
            operations.append(UpdateOne(query,{"$set":data},upsert=True))
        return self.bulk_write(operations) if operations else None

    def update_task(self,task_name,task_uploaded_date,batch,data):
        query={"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":batch}
        return self.update_one(query,{"$set":data})

    def update_student_track(self,task_name,task_uploaded_date,batch,student_roll_number,data):
        query={"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":batch,"track.student_roll_number":student_roll_number}
        return self.update_one(query,{"$set":{"track.$":data}})

    def delete_task(self,task_name,task_uploaded_date,batch):
        return self.delete_one({"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":batch})

    def get_task_names(self,batch=None):
        query={"batch":batch} if batch else {}
        return sorted(self.distinct("task_name",query))

    def get_batches(self):
        return sorted(self.distinct("batch"))

    @classmethod
    def get_by_faculty_batch_all(cls,department,faculty_id,batch):
        database=MongoManager.get_assignment_db(department)
        records=[]
        for collection_name in database.list_collection_names():
            documents=list(database[collection_name].find({"faculty_id":int(faculty_id),"batch":str(batch).strip()}))
            for document in documents: document["_collection_name"]=collection_name
            records.extend(documents)
        return records

    @classmethod
    def delete_refs(cls,department,refs):
        database=MongoManager.get_assignment_db(department)
        deleted=0
        for ref in refs:
            collection_name,document_id=str(ref).split("::",1)
            if ObjectId.is_valid(document_id): deleted+=database[collection_name].delete_one({"_id":ObjectId(document_id)}).deleted_count
        return deleted