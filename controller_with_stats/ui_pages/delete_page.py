import json
import pandas as pd
import streamlit as st
from config import Config
from utils.constants import Constants
from services.student_service import StudentService
from services.course_service import CourseService
from services.material_service import MaterialService
from services.curriculum_service import CurriculumService
from services.task_service import TaskService
from services.faculty_service import FacultyService

class DeletePage:
    def render(self):
        tabs=st.tabs(Constants.DELETE_TABS)
        with tabs[0]: self.delete_students()
        with tabs[1]: self.delete_subjects()
        with tabs[2]: self.delete_materials()
        with tabs[3]: self.delete_tasks()
        with tabs[4]: self.delete_curriculum()

    def delete_students(self):
        st.subheader("Delete Students")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="delete_students_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="delete_students_batch")
            sections=StudentService(department).get_sections(batch) if department else []
            section=st.selectbox("Select Section",["All Sections"]+sections,key="delete_students_section")
            load=st.button("Load Students",use_container_width=True,key="delete_students_load")
        if load and department:
            records=StudentService(department).get_students(batch)
            if section!="All Sections": records=[record for record in records if record.get("student_section")==section]
            self._load_records("delete_students_data",records)
        with col2:
            function=StudentService(department).delete_by_ids if department else None
            self._delete_editor("delete_students_data","Students",function)

    def delete_subjects(self):
        st.subheader("Delete Subjects")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="delete_subjects_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="delete_subjects_batch")
            service=CourseService(department) if department else None
            semesters=service.get_semesters(batch) if service else []
            semester=st.selectbox("Select Semester",["All Semesters"]+semesters,key="delete_subjects_semester")
            load=st.button("Load Subjects",use_container_width=True,key="delete_subjects_load")
        if load and service:
            records=service.get_courses(batch)
            if semester!="All Semesters": records=[record for record in records if int(record.get("semester",0))==int(semester)]
            self._load_records("delete_subjects_data",records)
        with col2:
            function=CourseService(department).delete_by_ids if department else None
            self._delete_editor("delete_subjects_data","Subjects",function)

    def delete_materials(self):
        st.subheader("Delete Materials")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="delete_materials_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="delete_materials_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="delete_materials_faculty")
            load=st.button("Load Materials",use_container_width=True,key="delete_materials_load")
        if load and department:
            service=MaterialService(department)
            records=service.get_materials(int(faculty_id),batch)
            self._load_records("delete_materials_data",records)
        with col2:
            function=MaterialService(department).delete_by_ids if department else None
            self._delete_editor("delete_materials_data","Materials",function)

    def delete_tasks(self):
        st.subheader("Delete Tasks")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="delete_tasks_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="delete_tasks_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="delete_tasks_faculty")
            load=st.button("Load Tasks",use_container_width=True,key="delete_tasks_load")
        if load and department:
            records=TaskService.get_all_for_faculty(department,int(faculty_id),batch)
            self._load_records("delete_tasks_data",records)
        with col2:
            function=(lambda refs:TaskService.delete_refs(department,refs)) if department else None
            self._delete_editor("delete_tasks_data","Tasks",function)
    def delete_curriculum(self):
        st.subheader("Delete Course Curriculum")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="delete_curriculum_department",wrap=True)
            batch=st.selectbox("Select Batch",Config.BATCHES,key="delete_curriculum_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="delete_curriculum_faculty")
            faculty_service=FacultyService(department) if department else None
            semesters=faculty_service.get_semesters(faculty_id,batch) if faculty_service else []
            semester=st.selectbox("Select Semester",semesters,key="delete_curriculum_semester") if semesters else None
            subjects=faculty_service.get_subjects(faculty_id,batch,semester) if faculty_service and semester is not None else []
            subject=st.selectbox("Select Subject",["All Subjects"]+subjects,key="delete_curriculum_subject") if subjects else None
            load=st.button("Load Curriculum",use_container_width=True,key="delete_curriculum_load")
        if load and department and semester is not None:
            records=CurriculumService(department).get_curriculums(faculty_id)
            records=[record for record in records if record.get("batch")==batch and int(record.get("semester",0))==int(semester)]
            if subject and subject!="All Subjects": records=[record for record in records if record.get("subject_name")==subject]
            self._load_records("delete_curriculum_data",records)
        with col2:
            function=CurriculumService(department).delete_by_ids if department else None
            self._delete_editor("delete_curriculum_data","Curriculum",function)

    def _load_records(self,state_key,records):
        dataframe=pd.DataFrame(records)
        if dataframe.empty:
            st.session_state[state_key]=pd.DataFrame()
            self._reset_editor(state_key)
            return
        if "_collection_name" in dataframe.columns:
            indexes=[f"{collection}::{document_id}" for collection,document_id in zip(dataframe["_collection_name"],dataframe["_id"])]
            dataframe=dataframe.drop(columns=["_id","_collection_name"])
        else:
            indexes=dataframe["_id"].astype(str).tolist()
            dataframe=dataframe.drop(columns=["_id"])
        for column in dataframe.columns: dataframe[column]=dataframe[column].apply(self._display_value)
        dataframe.insert(0,"Delete",False)
        dataframe.index=indexes
        dataframe.index.name="_mongo_ref"
        st.session_state[state_key]=dataframe
        self._reset_editor(state_key)

    def _delete_editor(self,state_key,label,delete_function):
        dataframe=st.session_state.get(state_key)
        if dataframe is None:
            st.info(f"Load {label.lower()} to continue")
            return
        if dataframe.empty:
            st.info(f"No {label.lower()} found")
            return
        action1,action2,action3=st.columns(3)
        if action1.button("Select All",use_container_width=True,key=f"{state_key}_select_all"):
            dataframe["Delete"]=True
            st.session_state[state_key]=dataframe
            self._reset_editor(state_key)
            st.rerun()
        if action2.button("Clear Selection",use_container_width=True,key=f"{state_key}_clear"):
            dataframe["Delete"]=False
            st.session_state[state_key]=dataframe
            self._reset_editor(state_key)
            st.rerun()
        selected_count=int(dataframe["Delete"].fillna(False).astype(bool).sum())
        action3.metric("Selected",selected_count)
        version=st.session_state.get(f"{state_key}_version",0)
        disabled=[column for column in dataframe.columns if column!="Delete"]
        edited=st.data_editor(dataframe,use_container_width=True,hide_index=True,num_rows="fixed",disabled=disabled,column_config={"Delete":st.column_config.CheckboxColumn("Delete",default=False)},key=f"{state_key}_editor_{version}")
        edited["Delete"]=edited["Delete"].fillna(False).astype(bool)
        st.session_state[state_key]=edited
        selected_ids=edited.index[edited["Delete"]].astype(str).tolist()
        st.caption(f"{len(selected_ids)} record(s) selected for deletion")
        if st.button(f"Delete Selected {label}",type="primary",use_container_width=True,disabled=not selected_ids or delete_function is None,key=f"{state_key}_delete"):
            result=delete_function(selected_ids)
            deleted=int(result.deleted_count) if hasattr(result,"deleted_count") else int(result or 0)
            if deleted==0:
                st.error("No records were deleted")
                return
            remaining=edited.drop(index=selected_ids,errors="ignore").copy()
            if not remaining.empty: remaining["Delete"]=False
            st.session_state[state_key]=remaining
            self._reset_editor(state_key)
            st.toast(f"{deleted} {label.lower()} deleted successfully")
            st.rerun()

    def _reset_editor(self,state_key):
        st.session_state[f"{state_key}_version"]=st.session_state.get(f"{state_key}_version",0)+1

    @staticmethod
    def _display_value(value):
        return json.dumps(value,ensure_ascii=False,default=str) if isinstance(value,(list,dict)) else value