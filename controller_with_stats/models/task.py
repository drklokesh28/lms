class TaskQuestion:
    def __init__(self,question_name,option_a,option_b,option_c,option_d,correct_option,marks):
        self.question_name=str(question_name).strip()
        self.option_a=str(option_a).strip()
        self.option_b=str(option_b).strip()
        self.option_c=str(option_c).strip()
        self.option_d=str(option_d).strip()
        self.correct_option=str(correct_option).strip()
        self.marks=float(marks)

    def to_dict(self):
        return {"question_name":self.question_name,"option_a":self.option_a,"option_b":self.option_b,"option_c":self.option_c,"option_d":self.option_d,"correct_option":self.correct_option,"marks":self.marks}


class TaskTrack:
    def __init__(self,student_name,student_roll_number,student_gender,student_batch,student_section,student_status="Incomplete",student_marks=0):
        self.student_name=str(student_name).strip()
        self.student_roll_number=str(student_roll_number).strip()
        self.student_gender=str(student_gender).strip()
        self.student_batch=str(student_batch).strip()
        self.student_section=str(student_section).strip()
        self.student_status=str(student_status).strip()
        self.student_marks=float(student_marks)

    def to_dict(self):
        return {"student_name":self.student_name,"student_roll_number":self.student_roll_number,"student_gender":self.student_gender,"student_batch":self.student_batch,"student_section":self.student_section,"student_status":self.student_status,"student_marks":self.student_marks}


class Task:
    def __init__(self,task_name,task_uploaded_date,batch,semester,subject_name,subject_type,faculty_id,sections,questions,track):
        self.task_name=str(task_name).strip()
        self.task_uploaded_date=str(task_uploaded_date).strip()
        self.batch=str(batch).strip()
        self.semester=int(semester)
        self.subject_name=str(subject_name).strip()
        self.subject_type=str(subject_type).strip()
        self.faculty_id=int(faculty_id)
        self.sections=[str(x).strip() for x in sections if str(x).strip()]
        self.questions=questions
        self.track=track

    def to_dict(self):
        return {"task_name":self.task_name,"task_uploaded_date":self.task_uploaded_date,"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_type":self.subject_type,"faculty_id":self.faculty_id,"sections":self.sections,"questions":[x.to_dict() if hasattr(x,"to_dict") else x for x in self.questions],"track":[x.to_dict() if hasattr(x,"to_dict") else x for x in self.track],"total_marks":sum(float(x.marks if hasattr(x,"marks") else x.get("marks",0)) for x in self.questions)}