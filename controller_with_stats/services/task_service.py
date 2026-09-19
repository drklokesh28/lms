from datetime import date
from models.task import Task,TaskQuestion,TaskTrack
from repositories.task_repository import TaskRepository
from repositories.student_repository import StudentRepository
from database.index_manager import IndexManager
from utils.csv_parser import CSVParser
from utils.validators import Validator
from utils.collection_names import CollectionName

class TaskService:
    def __init__(self,department,batch,semester,subject_name):
        self.department=department
        self.batch=batch
        self.semester=int(semester)
        self.subject_name=subject_name
        self.collection_name=CollectionName.task_collection(subject_name,batch,semester)
        self.repository=TaskRepository(department,self.collection_name)
        self.student_repository=StudentRepository(department)
        IndexManager.create_task_indexes(department,self.collection_name)

    def add_task(self,dataframe,task_name,subject_type,faculty_id,sections,task_uploaded_date=None):
        dataframe=CSVParser.parse_tasks(dataframe)
        questions=self._build_questions(dataframe)
        track=self._build_track(sections)
        task_uploaded_date=task_uploaded_date or date.today().isoformat()
        data={"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_type":subject_type,"faculty_id":faculty_id,"sections":sections,"questions":[question.to_dict() for question in questions]}
        if not Validator.validate_task(data):
            raise ValueError("Invalid task data")
        task=Task(task_name,task_uploaded_date,self.batch,self.semester,self.subject_name,subject_type,faculty_id,sections,questions,track)
        return self.repository.upsert_task(task)

    def get_tasks(self,faculty_id=None):
        return self.repository.get_tasks(self.batch,faculty_id)

    def get_task(self,task_name,task_uploaded_date):
        return self.repository.get_task(task_name,task_uploaded_date,self.batch)

    def update_task(self,dataframe,task_name,task_uploaded_date,subject_type,faculty_id,sections):
        dataframe=CSVParser.parse_tasks(dataframe)
        questions=self._build_questions(dataframe)
        current=self.get_task(task_name,task_uploaded_date)
        track=current.get("track",[]) if current else self._build_track(sections)
        data={"task_name":task_name,"task_uploaded_date":task_uploaded_date,"batch":self.batch,"semester":self.semester,"subject_name":self.subject_name,"subject_type":subject_type,"faculty_id":faculty_id,"sections":sections,"questions":[question.to_dict() for question in questions],"track":[item.to_dict() if hasattr(item,"to_dict") else item for item in track],"total_marks":sum(question.marks for question in questions)}
        return self.repository.update_task(task_name,task_uploaded_date,self.batch,data)

    def delete_task(self,task_name,task_uploaded_date):
        return self.repository.delete_task(task_name,task_uploaded_date,self.batch)

    def get_task_names(self):
        return self.repository.get_task_names(self.batch)

    def _build_questions(self,dataframe):
        questions=[]
        for record in dataframe.to_dict("records"):
            if Validator.validate_question(record):
                questions.append(TaskQuestion(**record))
        return questions

    def _build_track(self,sections):
        students=[]
        seen=set()
        for section in sections:
            for student in self.student_repository.get_by_batch_section(self.batch,section):
                key=student["student_roll_number"]
                if key in seen:
                    continue
                seen.add(key)
                students.append(TaskTrack(student["student_name"],student["student_roll_number"],student["student_gender"],student["student_batch"],student["student_section"]))
        return students

    def delete_by_ids(self,ids):
        return self.repository.delete_by_ids(ids)

    @classmethod
    def get_all_for_faculty(cls,department,faculty_id,batch):
        return TaskRepository.get_by_faculty_batch_all(department,int(faculty_id),batch)

    @classmethod
    def delete_refs(cls,department,refs):
        return TaskRepository.delete_refs(department,refs)