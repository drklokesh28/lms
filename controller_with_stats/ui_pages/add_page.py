import streamlit as st
import pandas as pd
from config import Config
from utils.constants import Constants
from utils.csv_parser import CSVParser
from services.student_service import StudentService
from services.course_service import CourseService
from services.material_service import MaterialService
from services.curriculum_service import CurriculumService
from services.task_service import TaskService
from services.faculty_service import FacultyService
from components.editors import Editors
from components.metrics import Metrics
from components.faculty_selector import FacultySelector

class AddPage:
    def render(self):
        tabs=st.tabs(Constants.ADD_TABS)
        with tabs[0]:
            self.add_department()
        with tabs[1]:
            self.add_subjects()
        with tabs[2]:
            self.add_materials()
        with tabs[3]:
            self.add_tasks()
        with tabs[4]:
            self.add_curriculum()

    def add_department(self):
        st.subheader("Add Department Students")

        col1,col2=st.columns(
            [1,2],
            border=True,
            gap="small"
        )

        with col1:
            department=st.pills(
                "Select Department",
                Config.DEPARTMENTS,
                key="add_students_department",
                wrap=True
            )

            batch=st.selectbox(
                "Select Batch",
                Config.BATCHES,
                key="add_students_batch"
            )

            file=st.file_uploader(
                "Upload Students File",
                type=["csv"],
                key="add_students_file"
            )

        if not file or not department:
            return

        dataframe=CSVParser.read(file)

        with col2:
            st.caption(
                "Required columns: Student Name, Semister, Roll Number, Gender, Section. Password is optional."
            )

            edited=Editors.dataframe(
                dataframe,
                "add_students_editor"
            )

            if st.button(
                "Add Students",
                use_container_width=True,
                key="add_students_button"
            ):
                try:
                    result=StudentService(
                        department
                    ).import_students(
                        edited,
                        batch
                    )

                    Metrics.student_import(result)

                    st.success(
                        f"Students processed successfully | Semister {result.get('semister')}"
                    )

                except (ValueError,KeyError) as error:
                    st.error(str(error))
                
    def add_subjects(self):
        st.subheader("Add Subjects")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="add_subjects_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="add_subjects_batch")
            file=st.file_uploader("Upload Subjects File",type=["csv"],key="add_subjects_file")
        if not file or not department:
            return
        dataframe=CSVParser.read(file)
        with col2:
            edited=Editors.dataframe(dataframe,"add_subjects_editor")
            if st.button("Add Subjects",use_container_width=True,key="add_subjects_button"):
                result=CourseService(department).import_courses(edited,batch)
                Metrics.course_import(result)
                st.success("Subjects processed successfully")

    def add_materials(self):
        st.subheader("Add Materials")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="add_material_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="add_material_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="add_material_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="add_material_auth")
        if not department:
            return
        if authenticate:
            st.session_state["add_material_authenticated"]=bool(FacultyService(department).get_courses(faculty_id,batch))
        if not st.session_state.get("add_material_authenticated",False):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("add_material")
            if not selection:
                return
            paths=Editors.paths("add_material_paths")
            if st.button("Add Materials",use_container_width=True,key="add_material_button"):
                MaterialService(department).add_material(batch,selection["semester"],selection["subject_name"],selection["subject_type"],faculty_id,paths,selection["sections"])
                st.success("Materials added successfully")

    def add_curriculum(self):
        st.subheader("Add Course Curriculum")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="add_curriculum_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="add_curriculum_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="add_curriculum_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="add_curriculum_auth")
        if not department:
            return
        if authenticate:
            st.session_state["add_curriculum_authenticated"]=bool(FacultyService(department).get_courses(faculty_id,batch))
        if not st.session_state.get("add_curriculum_authenticated",False):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("add_curriculum")
            if not selection:
                return
            file=st.file_uploader("Upload Curriculum File",type=["csv"],key="add_curriculum_file")
            if not file:
                return
            dataframe=CSVParser.read(file)
            edited=Editors.dataframe(dataframe,"add_curriculum_editor")
            if st.button("Add Curriculum",use_container_width=True,key="add_curriculum_button"):
                CurriculumService(department).add_curriculum(edited,batch,selection["semester"],selection["subject_name"],selection["subject_type"],faculty_id,selection["sections"])
                st.success("Course curriculum added successfully")

    def add_tasks(self):
        st.subheader("Add Tasks")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="add_task_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="add_task_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="add_task_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="add_task_auth")
        if not department:
            return
        if authenticate:
            st.session_state["add_task_authenticated"]=bool(FacultyService(department).get_courses(faculty_id,batch))
        if not st.session_state.get("add_task_authenticated",False):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("add_task")
            if not selection:
                return
            task_name=st.text_input("Task Name",key="add_task_name")
            task_date=st.date_input("Task Uploaded Date",key="add_task_date")
            file=st.file_uploader("Upload Questions File",type=["csv"],key="add_task_file")
            if not file:
                return
            dataframe=CSVParser.read(file)
            edited=Editors.dataframe(dataframe,"add_task_editor")
            if st.button("Add Task",use_container_width=True,key="add_task_button"):
                service=TaskService(department,batch,selection["semester"],selection["subject_name"])
                service.add_task(edited,task_name,selection["subject_type"],faculty_id,selection["sections"],task_date.isoformat())
                st.success("Task added successfully")