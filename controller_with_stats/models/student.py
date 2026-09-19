class Student:
    def __init__(self,student_name,student_roll_number,student_gender,student_batch,student_section,student_password,semister):
        self.student_name=str(student_name).strip()
        self.student_roll_number=str(student_roll_number).strip()
        self.student_gender=str(student_gender).strip()
        self.student_batch=str(student_batch).strip()
        self.student_section=str(student_section).strip()
        self.student_password=str(student_password).strip()
        self.semister=int(semister)

    def to_dict(self):
        return {
            "student_name":self.student_name,
            "student_roll_number":self.student_roll_number,
            "student_batch":self.student_batch,
            "semister":self.semister,
            "student_gender":self.student_gender,
            "student_section":self.student_section,
            "student_password":self.student_password
        }

    @classmethod
    def from_dict(cls,data):
        return cls(
            data["student_name"],
            data["student_roll_number"],
            data["student_gender"],
            data["student_batch"],
            data["student_section"],
            data["student_password"],
            data["semister"]
        )