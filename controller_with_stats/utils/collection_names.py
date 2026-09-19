import re

class CollectionName:
    @staticmethod
    def normalize(value):
        value=str(value).strip().lower()
        value=re.sub(r"[^a-z0-9]+","_",value)
        return value.strip("_")

    @classmethod
    def task_collection(cls,subject_name,batch,semester):
        subject=cls.normalize(subject_name)
        batch=cls.normalize(batch)
        semester=cls.normalize(f"semester_{semester}")
        return f"{subject}_{batch}_{semester}"