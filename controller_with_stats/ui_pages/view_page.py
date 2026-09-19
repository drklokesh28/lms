import streamlit as st
import pandas as pd
from config import Config
from utils.constants import Constants
from services.student_service import StudentService
from services.course_service import CourseService
from services.material_service import MaterialService
from services.curriculum_service import CurriculumService
from services.task_service import TaskService
from services.faculty_service import FacultyService
from components.editors import Editors
from components.faculty_selector import FacultySelector
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

class ViewPage:
    def render(self):
        tabs=st.tabs(Constants.VIEW_TABS)
        with tabs[0]:
            self.view_students()
        with tabs[1]:
            self.view_subjects()
        with tabs[2]:
            self.view_materials()
        with tabs[3]:
            self.view_tasks()
        with tabs[4]:
            self.view_curriculum()

    def view_students(self):
        st.subheader("View Students")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="view_students_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="view_students_batch")
            load=st.button("Load Students",use_container_width=True,key="view_students_load")
            keep=st.toggle("Keep Data Visible",value=True,key="view_students_keep")
        if load and department:
            data=StudentService(department).get_students(batch)
            st.session_state["view_students_data"]=pd.DataFrame(data).drop(columns=["_id"],errors="ignore")
        if not keep:
            st.session_state.pop("view_students_data",None)
        dataframe=st.session_state.get("view_students_data")
        if dataframe is None:
            return
        with col2:
            if dataframe.empty:
                st.info("No students found")
                return
            Editors.table(dataframe)
            st.metric("Total Students",len(dataframe))

    def view_subjects(self):
        st.subheader("View Subjects")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="view_subjects_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="view_subjects_batch")
        if not department:
            return
        service=CourseService(department)
        semesters=service.get_semesters(batch)
        if not semesters:
            with col2:
                st.info("No subjects found")
            return
        with col1:
            semester=st.selectbox("Select Semester",semesters,key="view_subjects_semester")
            load=st.button("Load Subjects",use_container_width=True,key="view_subjects_load")
            keep=st.toggle("Keep Data Visible",value=True,key="view_subjects_keep")
        if load:
            data=service.get_courses_by_semester(batch,semester)
            st.session_state["view_subjects_data"]=pd.DataFrame(data).drop(columns=["_id"],errors="ignore")
        if not keep:
            st.session_state.pop("view_subjects_data",None)
        dataframe=st.session_state.get("view_subjects_data")
        if dataframe is None:
            return
        with col2:
            if dataframe.empty:
                st.info("No subjects found")
                return
            Editors.table(dataframe)
            st.metric("Total Subjects",len(dataframe))

    def view_materials(self):
        st.subheader("View Materials")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="view_material_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="view_material_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="view_material_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="view_material_auth")
        if not department:
            return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(faculty_id,batch))
            st.session_state["view_material_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("view_material_auth_data")!=(department,batch,int(faculty_id)):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("view_material")
            if not selection:
                return
            material=MaterialService(department).get_material(batch,selection["semester"],selection["subject_name"],faculty_id)
            if not material:
                st.info("No materials found")
                return
            materials=material.get("materials",[])
            if not materials:
                st.info("No material paths found")
                return
            selected=st.selectbox("Select Material",materials,format_func=lambda value:Path(str(value)).name,key="view_material_path")
            path=self._resolve_material_path(selected)
            if not path.exists():
                st.error(f"Material file not found: {selected}")
                return
            if path.suffix.lower()!=".pdf":
                st.error("Selected material is not a PDF file")
                return
            pdf_viewer(input=str(path),width="100%",height=900,key=f"pdf_{path.name}")

    def view_curriculum(self):
        st.subheader("View Course Curriculum")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="view_curriculum_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="view_curriculum_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="view_curriculum_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="view_curriculum_auth")
        if not department:
            return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(faculty_id,batch))
            st.session_state["view_curriculum_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("view_curriculum_auth_data")!=(department,batch,int(faculty_id)):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("view_curriculum")
            if not selection:
                return
            curriculum=CurriculumService(department).get_curriculum(batch,selection["semester"],selection["subject_name"],faculty_id)
            if not curriculum:
                st.info("No curriculum found")
                return
            unit=st.selectbox("Select Unit",[1,2,3,4,5],key="view_curriculum_unit")
            topics=curriculum.get(f"unit_{unit}",[])
            dataframe=pd.DataFrame(topics)
            if dataframe.empty:
                st.info("No topics found")
                return
            Editors.table(dataframe)
            st.metric("Total Topics",len(dataframe))

    def view_tasks(self):
        st.subheader("View Tasks")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="view_task_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="view_task_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="view_task_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="view_task_auth")
        if not department:
            return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(faculty_id,batch))
            st.session_state["view_task_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("view_task_auth_data")!=(department,batch,int(faculty_id)):
            return
        with col2:
            selection=FacultySelector(department,faculty_id,batch).render("view_task")
            if not selection:
                return
            service=TaskService(department,batch,selection["semester"],selection["subject_name"])
            tasks=service.get_tasks(faculty_id)
            if not tasks:
                st.info("No tasks found")
                return
            labels=[f"{task['task_name']} | {task['task_uploaded_date']}" for task in tasks]
            selected_label=st.selectbox("Select Task",labels,key="view_task_select")
            task=tasks[labels.index(selected_label)]
            tab1,tab2=st.tabs(["Questions","Student Tracking"])
            with tab1:
                questions=pd.DataFrame(task.get("questions",[]))
                Editors.table(questions)
                st.metric("Total Marks",task.get("total_marks",0))
            with tab2:
                track=pd.DataFrame(task.get("track",[]))
                Editors.table(track)
                completed=len(track[track["student_status"]=="Completed"]) if not track.empty else 0
                incomplete=len(track)-completed
                metric1,metric2,metric3=st.columns(3)
                with metric1:
                    st.metric("Students",len(track))
                with metric2:
                    st.metric("Completed",completed)
                with metric3:
                    st.metric("Incomplete",incomplete)

    @staticmethod
    def _resolve_material_path(value):
        path=Path(str(value))
        if path.is_absolute():
            return path
        current=Path.cwd()/path
        parent=Path.cwd().parent/path
        return current if current.exists() else parent