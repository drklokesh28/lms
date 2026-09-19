from models.material import Material
from repositories.material_repository import MaterialRepository
from database.index_manager import IndexManager
from utils.validators import Validator
from utils.list_parser import ListParser

class MaterialService:
    def __init__(self,department):
        self.department=department
        self.repository=MaterialRepository(department)
        IndexManager.create_material_indexes(department)

    def add_material(self,batch,semester,subject_name,subject_type,faculty_id,materials,sections):
        data={"batch":batch,"semester":semester,"subject_name":subject_name,"subject_type":subject_type,"faculty_id":faculty_id,"materials":ListParser.parse_paths(materials),"sections":ListParser.parse_string_list(sections)}
        if not Validator.validate_material(data):
            raise ValueError("Invalid material data")
        material=Material.from_dict(data)
        return self.repository.upsert_material(material)

    def get_materials(self,faculty_id=None,batch=None):
        if faculty_id is not None and batch is not None: return self.repository.get_by_faculty_batch(int(faculty_id),batch)
        if faculty_id is not None: return self.repository.get_by_faculty(int(faculty_id))
        return self.repository.find()
    
    def get_material(self,batch,semester,subject_name,faculty_id):
        return self.repository.get_material(batch,semester,subject_name,faculty_id)

    def get_by_course(self,batch,semester,subject_name):
        return self.repository.get_by_course(batch,semester,subject_name)

    def update_material(self,batch,semester,subject_name,faculty_id,materials,sections,subject_type):
        data={"batch":batch,"semester":semester,"subject_name":subject_name,"subject_type":subject_type,"faculty_id":faculty_id,"materials":ListParser.parse_paths(materials),"sections":ListParser.parse_string_list(sections)}
        if not Validator.validate_material(data):
            raise ValueError("Invalid material data")
        material=Material.from_dict(data)
        return self.repository.update_material(batch,semester,subject_name,faculty_id,material.to_dict())

    def delete_material(self,batch,semester,subject_name,faculty_id):
        return self.repository.delete_material(batch,semester,subject_name,faculty_id)

    def get_batches(self):
        return self.repository.get_batches()

    def get_semesters(self,batch):
        return self.repository.get_semesters(batch)

    def get_subjects(self,batch,semester):
        return self.repository.get_subjects(batch,semester)

    def delete_by_ids(self,ids):
        return self.repository.delete_by_ids(ids)