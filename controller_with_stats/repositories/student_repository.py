from bson import ObjectId
from pymongo import UpdateOne
from config import Config
from database.mongo_client import MongoManager
from repositories.base_repository import BaseRepository


class StudentRepository(BaseRepository):

    def __init__(self,department):
        super().__init__(
            MongoManager.get_collection(
                department,
                Config.STUDENTS_COLLECTION
            )
        )

    @staticmethod
    def _batch(value):
        return str(value).strip()

    @staticmethod
    def _roll(value):
        return str(value).strip()

    def get_by_batch(self,batch):
        return self.find({
            "student_batch":self._batch(batch)
        })

    def get_by_batch_section(self,batch,section):
        return self.find({
            "student_batch":self._batch(batch),
            "student_section":str(section).strip()
        })

    def get_by_roll_number(self,roll_number,batch=None):
        query={
            "student_roll_number":self._roll(roll_number)
        }

        if batch is not None:
            query["student_batch"]=self._batch(batch)

        return self.find_one(query)

    def get_batches(self):
        values=self.distinct("student_batch")

        return sorted([
            str(value).strip()
            for value in values
            if str(value).strip()
        ])

    def get_sections(self,batch):
        values=self.distinct(
            "student_section",
            {
                "student_batch":self._batch(batch)
            }
        )

        return sorted([
            str(value).strip()
            for value in values
            if str(value).strip()
        ])

    def get_semisters(self,batch):
        values=self.distinct(
            "semister",
            {
                "student_batch":self._batch(batch)
            }
        )

        result=[]

        for value in values:
            try:
                value=int(value)

                if 1<=value<=8:
                    result.append(value)

            except:
                pass

        return sorted(set(result))

    def get_semister(self,batch):
        values=self.get_semisters(batch)

        if len(values)==1:
            return values[0]

        return None

    def upsert_students(self,students):
        operations=[]

        for student in students:
            data=student.to_dict()

            operations.append(
                UpdateOne(
                    {
                        "student_roll_number":data["student_roll_number"],
                        "student_batch":data["student_batch"]
                    },
                    {
                        "$set":data
                    },
                    upsert=True
                )
            )

        if not operations:
            return None

        return self.collection.bulk_write(
            operations,
            ordered=False
        )

    def update_student(self,old_roll_number,batch,data):
        return self.collection.update_one(
            {
                "student_roll_number":self._roll(old_roll_number),
                "student_batch":self._batch(batch)
            },
            {
                "$set":data
            }
        )

    def update_semister(self,batch,semister):
        return self.collection.update_many(
            {
                "student_batch":self._batch(batch)
            },
            {
                "$set":{
                    "semister":int(semister)
                }
            }
        )

    def delete_student(self,roll_number,batch):
        return self.collection.delete_one({
            "student_roll_number":self._roll(roll_number),
            "student_batch":self._batch(batch)
        })

    def delete_batch(self,batch):
        return self.collection.delete_many({
            "student_batch":self._batch(batch)
        })

    def delete_by_ids(self,ids):
        object_ids=[]

        for value in ids:
            if isinstance(value,ObjectId):
                object_ids.append(value)

            elif ObjectId.is_valid(str(value)):
                object_ids.append(
                    ObjectId(str(value))
                )

        if not object_ids:
            return self.collection.delete_many({
                "_id":{
                    "$in":[]
                }
            })

        return self.collection.delete_many({
            "_id":{
                "$in":object_ids
            }
        })

    def count_by_batch(self,batch):
        return self.collection.count_documents({
            "student_batch":self._batch(batch)
        })