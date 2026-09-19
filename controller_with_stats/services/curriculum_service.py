from models.curriculum import Curriculum
from repositories.curriculum_repository import CurriculumRepository
from database.index_manager import IndexManager
from utils.csv_parser import CSVParser
from utils.validators import Validator

class CurriculumService:
    def __init__(self,department):
        self.department=department
        self.repository=CurriculumRepository(department)
        IndexManager.create_curriculum_indexes(department)

    def add_curriculum(self,dataframe,batch,semester,subject_name,subject_type,faculty_id,sections):
        dataframe=CSVParser.parse_curriculum(dataframe)
        units=self._group_units(dataframe)
        data={"batch":str(batch).strip(),"semester":int(semester),"subject_name":str(subject_name).strip(),"subject_type":str(subject_type).strip(),"faculty_id":int(faculty_id),"sections":[str(section).strip() for section in sections],**units}
        if not Validator.validate_curriculum(data): raise ValueError("Invalid curriculum data")
        return self.repository.upsert_curriculum(Curriculum.from_dict(data))

    def get_curriculums(self,faculty_id=None,batch=None):
        if faculty_id is not None and batch is not None: return self.repository.get_by_faculty_batch(int(faculty_id),batch)
        if faculty_id is not None: return self.repository.get_by_faculty(int(faculty_id))
        return self.repository.find()

    def get_curriculum(self,batch,semester,subject_name,faculty_id):
        return self.repository.get_curriculum(batch,int(semester),subject_name,int(faculty_id))

    def get_by_course(self,batch,semester,subject_name):
        return self.repository.get_by_course(batch,int(semester),subject_name)

    def update_curriculum(self,dataframe,batch,semester,subject_name,subject_type,faculty_id,sections):
        dataframe=CSVParser.parse_curriculum(dataframe)
        units=self._group_units(dataframe)
        data={"batch":str(batch).strip(),"semester":int(semester),"subject_name":str(subject_name).strip(),"subject_type":str(subject_type).strip(),"faculty_id":int(faculty_id),"sections":[str(section).strip() for section in sections],**units}
        if not Validator.validate_curriculum(data): raise ValueError("Invalid curriculum data")
        return self.repository.update_curriculum(batch,int(semester),subject_name,int(faculty_id),Curriculum.from_dict(data).to_dict())

    def delete_curriculum(self,batch,semester,subject_name,faculty_id):
        return self.repository.delete_curriculum(batch,int(semester),subject_name,int(faculty_id))

    def delete_by_ids(self,ids):
        return self.repository.delete_by_ids(ids)

    def get_batches(self):
        return self.repository.get_batches()

    def get_semesters(self,batch):
        return self.repository.get_semesters(batch)

    def get_subjects(self,batch,semester):
        return self.repository.get_subjects(batch,int(semester))

    @staticmethod
    def _group_units(dataframe):
        units={f"unit_{number}":[] for number in range(1,6)}
        for record in dataframe.to_dict("records"):
            unit_number=int(record["unit_number"])
            if unit_number not in range(1,6): continue
            units[f"unit_{unit_number}"].append({"topic_name":str(record["topic_name"]).strip(),"yt_url":str(record["yt_url"]).strip(),"description":str(record["description"]).strip()})
        return units