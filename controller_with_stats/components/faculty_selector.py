import streamlit as st
from services.faculty_service import FacultyService

class FacultySelector:
    def __init__(self,department,faculty_id,batch):
        self.service=FacultyService(department)
        self.faculty_id=int(faculty_id)
        self.batch=batch

    def select_semester(self,key):
        semesters=self.service.get_semesters(self.faculty_id,self.batch)
        return st.selectbox("Select Semester",semesters,key=key) if semesters else None

    def select_subject(self,semester,key):
        subjects=self.service.get_subjects(self.faculty_id,self.batch,semester)
        return st.selectbox("Select Subject",subjects,key=key) if subjects else None

    def select_subject_type(self,semester,subject_name,key):
        types=self.service.get_subject_types(self.faculty_id,self.batch,semester,subject_name)
        return st.selectbox("Select Subject Type",types,key=key) if types else None

    def select_sections(self,semester,subject_name,key):
        sections=self.service.get_sections(self.faculty_id,self.batch,semester,subject_name)
        return st.multiselect("Select Sections",sections,default=sections,key=key) if sections else []

    def render(self,prefix="faculty",include_sections=True):
        semester=self.select_semester(f"{prefix}_semester")
        if semester is None:
            return None
        subject=self.select_subject(semester,f"{prefix}_subject")
        if subject is None:
            return None
        subject_type=self.select_subject_type(semester,subject,f"{prefix}_subject_type")
        available_sections=self.service.get_sections(self.faculty_id,self.batch,semester,subject)
        sections=self.select_sections(semester,subject,f"{prefix}_sections") if include_sections else available_sections
        return {"semester":semester,"subject_name":subject,"subject_type":subject_type,"sections":sections,"available_sections":available_sections}