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

class EditPage:
    def render(self):
        tabs=st.tabs(Constants.EDIT_TABS)
        with tabs[0]: self.edit_students()
        with tabs[1]: self.edit_subjects()
        with tabs[2]: self.edit_materials()
        with tabs[3]: self.edit_tasks()
        with tabs[4]: self.edit_curriculum()

    def edit_students(self):
        st.subheader("Edit Students")

        col1,col2=st.columns(
            [1,2],
            border=True,
            gap="small"
        )

        with col1:
            department=st.pills(
                "Select Department",
                Config.DEPARTMENTS,
                key="edit_students_department"
            )

            batch=st.selectbox(
                "Select Batch",
                Config.BATCHES,
                key="edit_students_batch"
            )

            load=st.button(
                "Load Students",
                use_container_width=True,
                key="edit_students_load"
            )

            keep=st.toggle(
                "Keep Data Visible",
                value=True,
                key="edit_students_keep"
            )

        if not department:
            return

        service=StudentService(department)

        if load:
            data=service.get_students(batch)

            if not data:
                st.session_state.pop(
                    "edit_students_data",
                    None
                )

                st.warning(
                    "No students found for this batch."
                )

                return

            dataframe=pd.DataFrame(data)

            dataframe=dataframe.drop(
                columns=[
                    "_id"
                ],
                errors="ignore"
            )

            if "semister" not in dataframe.columns:
                dataframe["semister"]=1

            dataframe=dataframe[
                [
                    "student_name",
                    "student_roll_number",
                    "student_batch",
                    "semister",
                    "student_gender",
                    "student_section",
                    "student_password"
                ]
            ]

            st.session_state["edit_students_data"]=dataframe

            st.session_state["edit_students_context"]=(
                department,
                batch
            )

        if not keep:
            st.session_state.pop(
                "edit_students_data",
                None
            )

            st.session_state.pop(
                "edit_students_context",
                None
            )

        dataframe=st.session_state.get(
            "edit_students_data"
        )

        if dataframe is None:
            return

        if st.session_state.get(
            "edit_students_context"
        )!=(department,batch):
            return

        with col2:
            edited=st.data_editor(
                dataframe,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                disabled=[
                    "student_batch"
                ],
                column_config={
                    "student_name":st.column_config.TextColumn(
                        "Student Name",
                        required=True
                    ),
                    "student_roll_number":st.column_config.TextColumn(
                        "Roll Number",
                        required=True
                    ),
                    "student_batch":st.column_config.TextColumn(
                        "Batch",
                        disabled=True
                    ),
                    "semister":st.column_config.NumberColumn(
                        "Semister",
                        min_value=1,
                        max_value=8,
                        step=1,
                        required=True
                    ),
                    "student_gender":st.column_config.SelectboxColumn(
                        "Gender",
                        options=[
                            "Male",
                            "Female"
                        ],
                        required=True
                    ),
                    "student_section":st.column_config.TextColumn(
                        "Section",
                        required=True
                    ),
                    "student_password":st.column_config.TextColumn(
                        "Password",
                        required=True
                    )
                },
                key="edit_students_editor"
            )

            if st.button(
                "Update Students",
                type="primary",
                use_container_width=True,
                key="edit_students_update"
            ):
                try:
                    original=pd.DataFrame(
                        service.get_students(batch)
                    )

                    original_rolls=set(
                        original["student_roll_number"].astype(str)
                    )

                    edited_rolls=set(
                        edited["student_roll_number"].astype(str)
                    )

                    for _,row in edited.iterrows():
                        service.update_student(
                            str(row["student_roll_number"]),
                            batch,
                            row.to_dict()
                        )

                    for roll in original_rolls-edited_rolls:
                        service.delete_student(
                            roll,
                            batch
                        )

                    st.session_state.pop(
                        "edit_students_data",
                        None
                    )

                    st.success(
                        "Students updated successfully."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(str(error))

    def edit_subjects(self):
        st.subheader("Edit Subjects")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="edit_subject_department")
            batch=st.selectbox("Select Batch",Config.BATCHES,key="edit_subject_batch")
            if not department: return
            service=CourseService(department)
            semesters=service.get_semesters(batch)
            if not semesters:
                st.info("No semesters found")
                return
            semester=st.selectbox("Select Semester",semesters,key="edit_subject_semester")
            courses=service.get_courses_by_semester(batch,semester)
            if not courses:
                st.info("No subjects found")
                return
            subject_names=[course["subject_name"] for course in courses]
            subject_name=st.selectbox("Select Subject",subject_names,key="edit_subject_select")
            subject=next(course for course in courses if course["subject_name"]==subject_name)
        with col2:
            widget_id=f"{semester}_{subject_names.index(subject_name)}"
            st.text_input("Subject Name",value=subject_name,disabled=True,key=f"edit_subject_name_{widget_id}")
            credits=st.number_input("Subject Credits",min_value=0.0,value=float(subject.get("subject_credits",0)),step=0.5,key=f"edit_subject_credits_{widget_id}")
            current_type=str(subject.get("subject_type","Theory"))
            type_index=Config.SUBJECT_TYPES.index(current_type) if current_type in Config.SUBJECT_TYPES else 0
            subject_type=st.selectbox("Subject Type",Config.SUBJECT_TYPES,index=type_index,key=f"edit_subject_type_{widget_id}")
            current_sections=",".join(str(value) for value in subject.get("allotted_sections",[]))
            current_faculty=",".join(str(value) for value in subject.get("allotted_faculty_ids",[]))
            sections_text=st.text_area("Allotted Sections",value=current_sections,placeholder="A,B,C,D,E",key=f"edit_subject_sections_{widget_id}")
            faculty_text=st.text_area("Allotted Faculty IDs",value=current_faculty,placeholder="5106,5107,5108,5109,5110",key=f"edit_subject_faculty_{widget_id}")
            try:
                preview_sections=self._parse_string_list(sections_text)
                preview_faculty=self._parse_int_list(faculty_text)
                preview_count=min(len(preview_sections),len(preview_faculty))
                if preview_count:
                    preview=pd.DataFrame({"Section":preview_sections[:preview_count],"Faculty ID":preview_faculty[:preview_count]})
                    st.dataframe(preview,use_container_width=True,hide_index=True)
            except ValueError:
                pass
            if st.button("Update Subject",type="primary",use_container_width=True,key=f"edit_subject_update_{widget_id}"):
                try:
                    sections=self._parse_string_list(sections_text)
                    faculty_ids=self._parse_int_list(faculty_text)
                    if not sections: raise ValueError("Enter at least one section")
                    if not faculty_ids: raise ValueError("Enter at least one faculty ID")
                    if len(sections)!=len(faculty_ids): raise ValueError(f"Faculty IDs count ({len(faculty_ids)}) must match sections count ({len(sections)})")
                    result=service.update_subject(batch,semester,subject_name,credits,subject_type,faculty_ids,sections)
                    if result.matched_count==0: raise ValueError("Subject was not found in MongoDB")
                    st.success("Subject updated successfully")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    def edit_materials(self):
        st.subheader("Edit Materials")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="edit_material_department")
            batch=st.selectbox("Select Batch",Config.BATCHES,key="edit_material_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="edit_material_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="edit_material_auth")
        if not department: return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(int(faculty_id),batch))
            st.session_state["edit_material_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("edit_material_auth_data")!=(department,batch,int(faculty_id)): return
        with col2:
            selection=FacultySelector(department,int(faculty_id),batch).render("edit_material_filter",include_sections=False)
            if not selection: return
            service=MaterialService(department)
            material=service.get_material(batch,selection["semester"],selection["subject_name"],int(faculty_id))
            if not material:
                st.info("No material record found")
                return
            paths="\n".join(material.get("materials",[]))
            sections=material.get("sections",[])
            new_paths=st.text_area("Material Paths",value=paths,key="edit_material_paths")
            new_sections=st.multiselect("Sections",selection["available_sections"],default=sections,key="edit_material_record_sections")
            if st.button("Update Materials",use_container_width=True,key="edit_material_update"):
                paths_value=",".join(path.strip() for path in new_paths.splitlines() if path.strip())
                service.update_material(batch,selection["semester"],selection["subject_name"],int(faculty_id),paths_value,new_sections,selection["subject_type"])
                st.success("Materials updated successfully")

    def edit_tasks(self):
        st.subheader("Edit Tasks")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="edit_task_department")
            batch=st.selectbox("Select Batch",Config.BATCHES,key="edit_task_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="edit_task_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="edit_task_auth")
        if not department: return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(int(faculty_id),batch))
            st.session_state["edit_task_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("edit_task_auth_data")!=(department,batch,int(faculty_id)): return
        with col2:
            selection=FacultySelector(department,int(faculty_id),batch).render("edit_task_filter",include_sections=False)
            if not selection: return
            service=TaskService(department,batch,selection["semester"],selection["subject_name"])
            tasks=service.get_tasks(int(faculty_id))
            if not tasks:
                st.info("No tasks found")
                return
            labels=[f"{task['task_name']} | {task['task_uploaded_date']}" for task in tasks]
            selected_label=st.selectbox("Select Task",labels,key="edit_task_select")
            selected_task=tasks[labels.index(selected_label)]
            questions=pd.DataFrame(selected_task.get("questions",[]))
            edited=Editors.dataframe(questions,"edit_task_editor")
            sections=st.multiselect("Sections",selection["available_sections"],default=selected_task.get("sections",[]),key="edit_task_record_sections")
            if st.button("Update Task",use_container_width=True,key="edit_task_update"):
                service.update_task(edited,selected_task["task_name"],selected_task["task_uploaded_date"],selection["subject_type"],int(faculty_id),sections)
                st.success("Task updated successfully")

    def edit_curriculum(self):
        st.subheader("Edit Course Curriculum")
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            department=st.pills("Select Department",Config.DEPARTMENTS,key="edit_curriculum_department")
            batch=st.selectbox("Select Batch",Config.BATCHES,key="edit_curriculum_batch")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="edit_curriculum_faculty")
            authenticate=st.button("Submit Faculty ID",use_container_width=True,key="edit_curriculum_auth")
        if not department: return
        if authenticate:
            valid=bool(FacultyService(department).get_courses(int(faculty_id),batch))
            st.session_state["edit_curriculum_auth_data"]=(department,batch,int(faculty_id)) if valid else None
        if st.session_state.get("edit_curriculum_auth_data")!=(department,batch,int(faculty_id)): return
        with col2:
            selection=FacultySelector(department,int(faculty_id),batch).render("edit_curriculum_filter",include_sections=False)
            if not selection: return
            service=CurriculumService(department)
            curriculum=service.get_curriculum(batch,selection["semester"],selection["subject_name"],int(faculty_id))
            if not curriculum:
                st.info("No curriculum found")
                return
            dataframe=self._curriculum_to_dataframe(curriculum)
            edited=Editors.dataframe(dataframe,"edit_curriculum_editor")
            sections=st.multiselect("Sections",selection["available_sections"],default=curriculum.get("sections",[]),key="edit_curriculum_record_sections")
            if st.button("Update Curriculum",use_container_width=True,key="edit_curriculum_update"):
                service.update_curriculum(edited,batch,selection["semester"],selection["subject_name"],selection["subject_type"],int(faculty_id),sections)
                st.success("Curriculum updated successfully")

    def _update_students(self,department,batch,original,edited):
        service=StudentService(department)
        original_map={row["student_roll_number"]:row for row in original.to_dict("records")}
        edited_map={row["student_roll_number"]:row for row in edited.to_dict("records")}
        for roll,row in edited_map.items(): service.update_student(roll,batch,row)
        for roll in set(original_map)-set(edited_map): service.delete_student(roll,batch)

    @staticmethod
    def _parse_int_list(value):
        values=[item.strip() for item in str(value).replace("[","").replace("]","").split(",") if item.strip()]
        try: return [int(item) for item in values]
        except ValueError: raise ValueError("Faculty IDs must contain only integer values separated by commas")

    @staticmethod
    def _parse_string_list(value):
        return [item.strip().replace("'","").replace('"',"") for item in str(value).replace("[","").replace("]","").split(",") if item.strip()]

    @staticmethod
    def _curriculum_to_dataframe(curriculum):
        rows=[]
        for unit_number in range(1,6):
            for topic in curriculum.get(f"unit_{unit_number}",[]): rows.append({"unit_number":unit_number,"topic_name":topic.get("topic_name",""),"yt_url":topic.get("yt_url",""),"description":topic.get("description","")})
        return pd.DataFrame(rows)