import streamlit as st
import pandas as pd
from config import Config
from services.stats_service import StatsService
from utils.report_generator import ReportGenerator

class StatsPage:
    def render(self):
        st.title("Statistics & Analytics")
        tabs=st.tabs(["Analyze Tasks Performance","Analyze Subject Study","Analyze Overall Performance Time"])
        with tabs[0]: self.task_performance()
        with tabs[1]: self.subject_study()
        with tabs[2]: self.overall_performance()

    @staticmethod
    def _select_section(sections,key):
        if not sections:
            st.warning("No sections are allotted to this faculty for the selected subject.")
            return None
        if len(sections)==1:
            st.selectbox("Select Section",sections,index=0,disabled=True,key=f"{key}_display")
            return sections[0]
        return st.selectbox("Select Section",sections,index=None,placeholder="Select section",key=key)

    def _faculty_subject_filters(self,prefix):
        faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key=f"{prefix}_faculty")
        department=st.selectbox("Select Department",Config.DEPARTMENTS,index=None,placeholder="Select department",key=f"{prefix}_department")
        if not department: return None
        service=StatsService(department)
        batches=service.get_faculty_batches(faculty_id)
        if not batches:
            st.warning("No courses are allotted to this faculty ID in the selected department.")
            return None
        batch=st.selectbox("Select Batch",batches,index=None,placeholder="Select batch",key=f"{prefix}_batch")
        if not batch: return None
        semesters=service.get_faculty_semesters(faculty_id,batch)
        semester=st.selectbox("Select Semester",semesters,index=None,placeholder="Select semester",key=f"{prefix}_semester") if semesters else None
        if semester is None: return None
        subjects=service.get_faculty_subjects(faculty_id,batch,semester)
        subject=st.selectbox("Select Subject",subjects,index=None,placeholder="Select subject",key=f"{prefix}_subject") if subjects else None
        if not subject: return None
        section=self._select_section(service.get_faculty_sections(faculty_id,batch,semester,subject),f"{prefix}_section")
        if not section: return None
        return {"service":service,"faculty_id":int(faculty_id),"department":department,"batch":batch,"semester":int(semester),"subject":subject,"section":section}

    @staticmethod
    def _metrics(metrics,prefix):
        items=list(metrics.items())
        for start in range(0,len(items),4):
            columns=st.columns(min(4,len(items)-start))
            for column,(label,value) in zip(columns,items[start:start+4]): column.metric(label,value)

    @staticmethod
    def _show_frame(title,frame):
        st.subheader(title)
        if frame is None or frame.empty: st.info("No records available.")
        else: st.dataframe(frame,hide_index=True,use_container_width=True)

    def task_performance(self):
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            st.subheader("Faculty & Course")
            filters=self._faculty_subject_filters("stats_task")
            analyze=st.toggle("Analyze Task Performance",key="stats_task_toggle",disabled=not bool(filters))
        if not filters or not analyze: return
        service=filters["service"]
        tasks=service.get_tasks(filters["faculty_id"],filters["batch"],filters["semester"],filters["subject"],filters["section"])
        with col2:
            if not tasks:
                st.warning("No tasks are available for the selected faculty, subject and section.")
                return
            labels=[f"{x.get('task_name','Task')} | {x.get('task_uploaded_date','')}" for x in tasks]
            selected=st.selectbox("Select Task Name",labels,key="stats_task_name")
            task=tasks[labels.index(selected)]
            performance=service.task_performance(task,filters["section"])
            metrics=service.task_metrics(performance)
            groups=service.task_groups(performance)
            st.subheader(task.get("task_name","Task"))
            st.caption(f"Subject: {filters['subject']} | Semester: {filters['semester']} | Section: {filters['section']} | Faculty ID: {filters['faculty_id']} | Uploaded: {task.get('task_uploaded_date','-')} | Pass Threshold: 50%")
            self._metrics(metrics,"task")
            self._show_frame("All Students",performance)
            task_pdf=ReportGenerator.build("Task Performance Report",{"Department":filters["department"],"Batch":filters["batch"],"Semester":filters["semester"],"Subject":filters["subject"],"Section":filters["section"],"Faculty ID":filters["faculty_id"],"Task":task.get("task_name",""),"Uploaded Date":task.get("task_uploaded_date","")},metrics,[("Student Performance",performance)])
            st.download_button("Download Task Report PDF",task_pdf,file_name=f"task_{task.get('task_name','report').replace(' ','_')}.pdf",mime="application/pdf",use_container_width=True,key="download_task_pdf")
            self._show_frame("Rank 1 - Highest Marks",groups["rank1"])
            self._show_frame("Rank 2",groups["rank2"])
            self._show_frame("Rank 3",groups["rank3"])
            self._show_frame("Failed Students",groups["failed"])
            self._show_frame("Passed Students - Male",groups["passed_male"])
            self._show_frame("Passed Students - Female",groups["passed_female"])
            self._show_frame("Failed Students - Male",groups["failed_male"])
            self._show_frame("Failed Students - Female",groups["failed_female"])
            sections=[("All Students",performance),("Rank 1 - Highest Marks",groups["rank1"]),("Rank 2",groups["rank2"]),("Rank 3",groups["rank3"]),("Failed Students",groups["failed"]),("Passed Students - Male",groups["passed_male"]),("Passed Students - Female",groups["passed_female"]),("Failed Students - Male",groups["failed_male"]),("Failed Students - Female",groups["failed_female"])]
            overall_pdf=ReportGenerator.build("Complete Task Analytics Report",{"Department":filters["department"],"Batch":filters["batch"],"Semester":filters["semester"],"Subject":filters["subject"],"Section":filters["section"],"Faculty ID":filters["faculty_id"],"Task":task.get("task_name",""),"Total Marks":task.get("total_marks",0),"Pass Threshold":"50%"},metrics,sections)
            st.download_button("Download Overall Task Analytics PDF",overall_pdf,file_name=f"task_complete_{task.get('task_name','analytics').replace(' ','_')}.pdf",mime="application/pdf",use_container_width=True,key="download_task_overall_pdf")

    def subject_study(self):
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            st.subheader("Faculty & Subject")
            filters=self._faculty_subject_filters("stats_subject")
            analyze=st.toggle("Analyze Subject Study",key="stats_subject_toggle",disabled=not bool(filters))
        if not filters or not analyze: return
        service=filters["service"]
        summary,daily,sessions=service.subject_study(filters["batch"],filters["semester"],filters["subject"],filters["section"])
        metrics=service.subject_metrics(summary)
        with col2:
            mode=st.radio("Analysis Mode",["All Students","Individual Student"],horizontal=True,key="stats_subject_mode")
            if mode=="All Students":
                st.subheader(f"{filters['subject']} - Section {filters['section']}")
                self._metrics(metrics,"subject")
                self._show_frame("Student-wise Subject Study Summary",summary)
                self._show_frame("Date-wise Study Performance",daily)
                report=ReportGenerator.build("Subject Study Analytics Report",{"Department":filters["department"],"Batch":filters["batch"],"Semester":filters["semester"],"Subject":filters["subject"],"Section":filters["section"],"Faculty ID":filters["faculty_id"]},metrics,[("Student-wise Summary",summary),("Date-wise Study Performance",daily),("Individual Sessions",sessions)])
                st.download_button("Download Subject Study Report PDF",report,file_name=f"subject_{filters['subject'].replace(' ','_')}_{filters['section']}.pdf",mime="application/pdf",use_container_width=True,key="download_subject_all")
            else:
                if summary.empty:
                    st.info("No students are available for this section.")
                    return
                choices={f"{row['Student Name']} | {row['Roll Number']}":row["Roll Number"] for _,row in summary.iterrows()}
                label=st.selectbox("Select Student",list(choices.keys()),key="stats_subject_student")
                roll=choices[label]
                student_summary=summary[summary["Roll Number"].astype(str)==str(roll)].copy()
                student_daily=daily[daily["Roll Number"].astype(str)==str(roll)].copy() if not daily.empty else daily.copy()
                student_sessions=sessions[sessions["Roll Number"].astype(str)==str(roll)].copy() if not sessions.empty else sessions.copy()
                row=student_summary.iloc[0]
                individual_metrics={"Study Days":int(row["Study Days"]),"Total Sessions":int(row["Total Sessions"]),"Total Minutes":row["Total Minutes"],"Total Hours":row["Total Hours"],"Average Minutes / Study Day":row["Average Minutes / Study Day"],"Last Study Date":row["Last Study Date"]}
                st.subheader(label)
                self._metrics(individual_metrics,"subject_individual")
                self._show_frame("Student Summary",student_summary)
                self._show_frame("Date-wise Performance",student_daily)
                self._show_frame("Session Details",student_sessions)
                report=ReportGenerator.build("Individual Subject Study Report",{"Department":filters["department"],"Batch":filters["batch"],"Semester":filters["semester"],"Subject":filters["subject"],"Section":filters["section"],"Faculty ID":filters["faculty_id"],"Student":label},individual_metrics,[("Student Summary",student_summary),("Date-wise Performance",student_daily),("Session Details",student_sessions)])
                st.download_button("Download Individual Subject Report PDF",report,file_name=f"subject_student_{roll}.pdf",mime="application/pdf",use_container_width=True,key="download_subject_individual")

    def overall_performance(self):
        col1,col2=st.columns([1,2],border=True,gap="small")
        with col1:
            st.subheader("Faculty & Student")
            faculty_id=st.number_input("Enter Faculty ID",min_value=1,step=1,key="stats_overall_faculty")
            department=st.selectbox("Select Department",Config.DEPARTMENTS,index=None,placeholder="Select department",key="stats_overall_department")
            if not department: return
            service=StatsService(department)
            batches=service.get_faculty_batches(faculty_id)
            if not batches:
                st.warning("No courses are allotted to this faculty ID.")
                return
            batch=st.selectbox("Select Batch",batches,index=None,placeholder="Select batch",key="stats_overall_batch")
            if not batch: return
            sections=service.get_faculty_batch_sections(faculty_id,batch)
            section=self._select_section(sections,"stats_overall_section")
            if not section: return
            students=service.get_section_students(batch,section)
            if not students:
                st.warning("No students are available in this section.")
                return
            choices={f"{x.get('student_name','')} | {x.get('student_roll_number','')}":str(x.get("student_roll_number","")) for x in students}
            student_label=st.selectbox("Select Student",list(choices.keys()),index=None,placeholder="Select student",key="stats_overall_student")
            analyze=st.toggle("Analyze Overall Performance",key="stats_overall_toggle",disabled=not bool(student_label))
        if not student_label or not analyze: return
        roll=choices[student_label]
        student,daily,sessions,metrics=service.overall_student_activity(batch,section,roll)
        with col2:
            if not student:
                st.warning("Student activity could not be found.")
                return
            st.subheader(student_label)
            st.caption(f"Department: {department} | Batch: {batch} | Section: {section} | Faculty ID: {faculty_id}")
            self._metrics(metrics,"overall")
            self._show_frame("Daily Overall Activity",daily)
            self._show_frame("All Overall Sessions",sessions)
            report=ReportGenerator.build("Overall Student Activity Report",{"Department":department,"Batch":batch,"Section":section,"Faculty ID":int(faculty_id),"Student Name":student.get("student_name",""),"Roll Number":roll,"Gender":student.get("student_gender","")},metrics,[("Daily Overall Activity",daily),("Overall Session Details",sessions)])
            st.download_button("Download Overall Performance PDF",report,file_name=f"overall_activity_{roll}.pdf",mime="application/pdf",use_container_width=True,key="download_overall_student")
