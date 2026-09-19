class Curriculum:
    def __init__(self,batch,semester,subject_name,subject_type,faculty_id,sections,unit_1=None,unit_2=None,unit_3=None,unit_4=None,unit_5=None):
        self.batch=str(batch).strip()
        self.semester=int(semester)
        self.subject_name=str(subject_name).strip()
        self.subject_type=str(subject_type).strip()
        self.faculty_id=int(faculty_id)
        self.sections=[str(section).strip() for section in sections if str(section).strip()]
        self.unit_1=unit_1 or []
        self.unit_2=unit_2 or []
        self.unit_3=unit_3 or []
        self.unit_4=unit_4 or []
        self.unit_5=unit_5 or []

    def to_dict(self):
        return {"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_type":self.subject_type,"faculty_id":self.faculty_id,"sections":self.sections,"unit_1":self.unit_1,"unit_2":self.unit_2,"unit_3":self.unit_3,"unit_4":self.unit_4,"unit_5":self.unit_5}

    @classmethod
    def from_dict(cls,data):
        return cls(data["batch"],data["semester"],data["subject_name"],data["subject_type"],data["faculty_id"],data["sections"],data.get("unit_1",[]),data.get("unit_2",[]),data.get("unit_3",[]),data.get("unit_4",[]),data.get("unit_5",[]))