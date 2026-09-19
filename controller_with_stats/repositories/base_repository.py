from bson import ObjectId

class BaseRepository:
    def __init__(self,collection):
        self.collection=collection

    def find(self,query=None,projection=None):
        return list(self.collection.find(query or {},projection))

    def find_one(self,query,projection=None):
        return self.collection.find_one(query,projection)

    def insert_one(self,document):
        return self.collection.insert_one(document)

    def insert_many(self,documents):
        return self.collection.insert_many(documents,ordered=False)

    def update_one(self,query,update,upsert=False):
        return self.collection.update_one(query,update,upsert=upsert)

    def update_many(self,query,update,upsert=False):
        return self.collection.update_many(query,update,upsert=upsert)

    def replace_one(self,query,document,upsert=False):
        return self.collection.replace_one(query,document,upsert=upsert)

    def delete_one(self,query):
        return self.collection.delete_one(query)

    def delete_many(self,query):
        return self.collection.delete_many(query)

    def delete_by_ids(self,ids):
        mongo_ids=[value if isinstance(value,ObjectId) else ObjectId(str(value).strip()) if ObjectId.is_valid(str(value).strip()) else value for value in ids]
        return self.collection.delete_many({"_id":{"$in":mongo_ids}})

    def count(self,query=None):
        return self.collection.count_documents(query or {})

    def bulk_write(self,operations,ordered=False):
        return self.collection.bulk_write(operations,ordered=ordered)

    def distinct(self,field,query=None):
        return self.collection.distinct(field,query or {})

    def aggregate(self,pipeline):
        return list(self.collection.aggregate(pipeline))