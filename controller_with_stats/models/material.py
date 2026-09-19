class Material:
    def __init__(self,batch,semester,subject_name,subject_type,faculty_id,materials,sections):
        self.batch=str(batch).strip()
        self.semester=int(semester)
        self.subject_name=str(subject_name).strip()
        self.subject_type=str(subject_type).strip()
        self.faculty_id=int(faculty_id)
        self.materials=[str(x).strip() for x in materials if str(x).strip()]
        self.sections=[str(x).strip() for x in sections if str(x).strip()]

    def to_dict(self):
        return {"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_type":self.subject_type,"faculty_id":self.faculty_id,"materials":self.materials,"sections":self.sections}

    @classmethod
    def from_dict(cls,data):
        return cls(data["batch"],data["semester"],data["subject_name"],data["subject_type"],data["faculty_id"],data["materials"],data["sections"])