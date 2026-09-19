class Course:
    def __init__(self,batch,semester,subject_name,subject_credits,subject_type,allotted_faculty_ids,allotted_sections):
        self.batch=str(batch).strip()
        self.semester=int(semester)
        self.subject_name=str(subject_name).strip()
        self.subject_credits=float(subject_credits)
        self.subject_type=str(subject_type).strip()
        self.allotted_faculty_ids=[int(x) for x in allotted_faculty_ids]
        self.allotted_sections=[str(x).strip() for x in allotted_sections]

    def validate(self):
        return len(self.allotted_faculty_ids)==len(self.allotted_sections)

    def to_dict(self):
        return {"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_credits":self.subject_credits,"subject_type":self.subject_type,"allotted_faculty_ids":self.allotted_faculty_ids,"allotted_sections":self.allotted_sections}

    @classmethod
    def from_dict(cls,data):
        return cls(data["batch"],data["semester"],data["subject_name"],data["subject_credits"],data["subject_type"],data["allotted_faculty_ids"],data["allotted_sections"])