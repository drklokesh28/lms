from datetime import datetime,date,time
import pandas as pd
from database.mongo_client import MongoManager
from repositories.student_repository import StudentRepository
from services.faculty_service import FacultyService
from utils.collection_names import CollectionName

class StatsService:
    def __init__(self,department):
        self.department=department
        self.faculty=FacultyService(department)
        self.students=StudentRepository(department)
        self.activity_db=MongoManager.get_client()[f"{department}_students_activity_logs"]

    @staticmethod
    def _text(value): return str(value).strip() if value is not None else ""

    @staticmethod
    def _number(value):
        try: return float(value)
        except: return 0.0

    @staticmethod
    def _date(value):
        if isinstance(value,datetime): return value.date()
        if isinstance(value,date): return value
        text=str(value or "").strip()
        if not text: return None
        try: return datetime.fromisoformat(text.replace("Z","+00:00")).date()
        except: pass
        for fmt in ("%Y-%m-%d","%d-%m-%Y","%d/%m/%Y","%Y/%m/%d"):
            try: return datetime.strptime(text,fmt).date()
            except: pass
        return None

    @staticmethod
    def _time(value):
        if isinstance(value,datetime): return value.strftime("%I:%M:%S %p")
        if isinstance(value,time): return value.strftime("%I:%M:%S %p")
        text=str(value or "").strip()
        if not text: return "-"
        for fmt in ("%H:%M:%S","%H:%M","%I:%M:%S %p","%I:%M %p"):
            try: return datetime.strptime(text,fmt).strftime("%I:%M:%S %p")
            except: pass
        return text

    @classmethod
    def _clock_seconds(cls,value):
        if isinstance(value,datetime): return value.hour*3600+value.minute*60+value.second
        if isinstance(value,time): return value.hour*3600+value.minute*60+value.second
        text=str(value or "").strip()
        for fmt in ("%H:%M:%S","%H:%M","%I:%M:%S %p","%I:%M %p"):
            try:
                parsed=datetime.strptime(text,fmt)
                return parsed.hour*3600+parsed.minute*60+parsed.second
            except: pass
        return None

    @classmethod
    def session_seconds(cls,session,overall=False):
        if session.get("duration_seconds") is not None: return max(0,cls._number(session.get("duration_seconds")))
        hours=cls._number(session.get("hours_studied" if overall else "hours_spent",0))
        minutes=cls._number(session.get("minutes_spent",0))
        if hours or minutes: return max(0,hours*3600+minutes*60)
        start=cls._clock_seconds(session.get("start_time"))
        end=cls._clock_seconds(session.get("end_time"))
        if start is None or end is None: return 0.0
        if end<start: end+=86400
        return max(0,end-start)

    def get_faculty_batches(self,faculty_id):
        return sorted({self._text(x.get("batch")) for x in self.faculty.get_courses(int(faculty_id)) if self._text(x.get("batch"))})

    def get_faculty_semesters(self,faculty_id,batch):
        return self.faculty.get_semesters(int(faculty_id),str(batch))

    def get_faculty_subjects(self,faculty_id,batch,semester):
        return self.faculty.get_subjects(int(faculty_id),str(batch),int(semester))

    def get_faculty_sections(self,faculty_id,batch,semester,subject):
        return self.faculty.get_sections(int(faculty_id),str(batch),int(semester),str(subject))

    def get_faculty_batch_sections(self,faculty_id,batch):
        sections=set()
        for course in self.faculty.get_courses(int(faculty_id),str(batch)):
            faculty_ids=course.get("allotted_faculty_ids",[])
            allotted_sections=course.get("allotted_sections",[])
            for faculty_id_value,section in zip(faculty_ids,allotted_sections):
                try:
                    if int(faculty_id_value)==int(faculty_id) and self._text(section): sections.add(self._text(section))
                except: pass
        return sorted(sections)

    def get_section_students(self,batch,section):
        return self.students.get_by_batch_section(str(batch),str(section))

    def get_tasks(self,faculty_id,batch,semester,subject,section):
        if str(section) not in self.get_faculty_sections(faculty_id,batch,semester,subject): return []
        collection=MongoManager.get_assignment_collection(self.department,CollectionName.task_collection(subject,batch,semester))
        query={"faculty_id":int(faculty_id),"batch":str(batch),"semester":int(semester),"subject_name":str(subject),"sections":str(section)}
        return list(collection.find(query).sort([("task_uploaded_date",-1),("task_name",1)]))

    def task_performance(self,task,section):
        total=float(task.get("total_marks",0) or 0)
        rows=[]
        for item in task.get("track",[]):
            if self._text(item.get("student_section"))!=self._text(section): continue
            marks=float(item.get("student_marks",0) or 0)
            status=self._text(item.get("student_status")) or "Incomplete"
            completed=status.lower()=="completed"
            percentage=(marks/total*100) if total>0 else 0
            result="Pass" if completed and percentage>=50 else "Fail" if completed else "Not Attempted"
            rows.append({"Student Name":item.get("student_name",""),"Roll Number":self._text(item.get("student_roll_number")),"Gender":self._text(item.get("student_gender")),"Marks Obtained":marks,"Total Marks":total,"Percentage":round(percentage,2),"Result":result,"Status":"✅ Completed" if completed else "❌ Incomplete"})
        return pd.DataFrame(rows)

    @staticmethod
    def task_groups(dataframe):
        if dataframe.empty:
            empty=dataframe.copy()
            return {"rank1":empty,"rank2":empty,"rank3":empty,"failed":empty,"passed_male":empty,"passed_female":empty,"failed_male":empty,"failed_female":empty}
        completed=dataframe[dataframe["Status"].astype(str).str.contains("Completed",case=False,na=False)].copy()
        marks=sorted(completed["Marks Obtained"].dropna().unique(),reverse=True)
        rank=lambda index: completed[completed["Marks Obtained"]==marks[index]].copy() if len(marks)>index else completed.iloc[0:0].copy()
        passed=completed[completed["Result"]=="Pass"].copy()
        failed=completed[completed["Result"]=="Fail"].copy()
        gender=lambda frame,value: frame[frame["Gender"].astype(str).str.lower()==value].copy()
        return {"rank1":rank(0),"rank2":rank(1),"rank3":rank(2),"failed":failed,"passed_male":gender(passed,"male"),"passed_female":gender(passed,"female"),"failed_male":gender(failed,"male"),"failed_female":gender(failed,"female")}

    @staticmethod
    def task_metrics(dataframe):
        if dataframe.empty: return {"Total Students":0,"Completed":0,"Incomplete":0,"Passed":0,"Failed":0,"Average %":0,"Highest Marks":0,"Lowest Marks":0}
        completed=dataframe[dataframe["Status"].astype(str).str.contains("Completed",case=False,na=False)]
        return {
            "Total Students":len(dataframe),
            "Completed":len(completed),
            "Incomplete":len(dataframe)-len(completed),
            "Passed":int((dataframe["Result"]=="Pass").sum()),
            "Failed":int((dataframe["Result"]=="Fail").sum()),
            "Average %":round(float(completed["Percentage"].mean()),2) if not completed.empty else 0,
            "Highest Marks":float(completed["Marks Obtained"].max()) if not completed.empty else 0,
            "Lowest Marks":float(completed["Marks Obtained"].min()) if not completed.empty else 0
        }

    def _activity_student(self,collection_name,batch,section,roll):
        collection=self.activity_db[collection_name]
        query={"batch":str(batch),"students_list":{"$elemMatch":{"student_roll_number":str(roll),"student_section":str(section)}}}
        document=collection.find_one(query) or {}
        return next((x for x in document.get("students_list",[]) if self._text(x.get("student_roll_number"))==self._text(roll) and self._text(x.get("student_section"))==self._text(section)),{})

    def subject_study(self,batch,semester,subject,section):
        students=self.get_section_students(batch,section)
        summary=[]
        daily_rows=[]
        session_rows=[]
        for student in students:
            roll=self._text(student.get("student_roll_number"))
            activity=self._activity_student("activity_logs",batch,section,roll)
            target=None
            for track in activity.get("tracks",activity.get("tarcks",[])):
                track_semester=self._text(track.get("subject_semister",track.get("subject_semester")))
                if self._text(track.get("subject_name"))==self._text(subject) and track_semester==self._text(semester):
                    target=track
                    break
            total_seconds=0.0
            total_sessions=0
            study_dates=[]
            if target:
                for day in target.get("track_subjects",[]):
                    parsed_date=self._date(day.get("date"))
                    sessions=day.get("sessions",[])
                    if isinstance(sessions,dict): sessions=[sessions]
                    day_seconds=0.0
                    for index,session in enumerate(sessions,1):
                        seconds=self.session_seconds(session,False)
                        day_seconds+=seconds
                        total_seconds+=seconds
                        total_sessions+=1
                        session_rows.append({"Student Name":student.get("student_name",""),"Roll Number":roll,"Gender":student.get("student_gender",""),"Date":parsed_date.strftime("%d-%m-%Y") if parsed_date else "-","Day":parsed_date.strftime("%A") if parsed_date else "-","Session":index,"Start Time":self._time(session.get("start_time")),"End Time":self._time(session.get("end_time")),"Seconds":round(seconds,2),"Minutes":round(seconds/60,2),"Hours":round(seconds/3600,3)})
                    if parsed_date and sessions:
                        study_dates.append(parsed_date)
                        daily_rows.append({"Student Name":student.get("student_name",""),"Roll Number":roll,"Gender":student.get("student_gender",""),"Date":parsed_date.strftime("%d-%m-%Y"),"Day":parsed_date.strftime("%A"),"Total Sessions":len(sessions),"Total Seconds":round(day_seconds,2),"Total Minutes":round(day_seconds/60,2),"Total Hours":round(day_seconds/3600,3)})
            unique_dates=sorted(set(study_dates))
            summary.append({"Student Name":student.get("student_name",""),"Roll Number":roll,"Gender":student.get("student_gender",""),"Study Days":len(unique_dates),"Total Sessions":total_sessions,"Total Seconds":round(total_seconds,2),"Total Minutes":round(total_seconds/60,2),"Total Hours":round(total_seconds/3600,3),"Average Minutes / Study Day":round((total_seconds/60/len(unique_dates)),2) if unique_dates else 0,"Last Study Date":unique_dates[-1].strftime("%d-%m-%Y") if unique_dates else "Not Studied"})
        return pd.DataFrame(summary),pd.DataFrame(daily_rows),pd.DataFrame(session_rows)

    @staticmethod
    def subject_metrics(summary):
        if summary.empty: return {"Total Students":0,"Studied Students":0,"Not Studied":0,"Total Sessions":0,"Total Hours":0,"Average Hours / Student":0,"Highest Study Hours":0,"Total Study Days":0}
        studied=summary[summary["Total Sessions"]>0]
        return {
            "Total Students":len(summary),
            "Studied Students":len(studied),
            "Not Studied":len(summary)-len(studied),
            "Total Sessions":int(summary["Total Sessions"].sum()),
            "Total Hours":round(float(summary["Total Hours"].sum()),2),
            "Average Hours / Student":round(float(summary["Total Hours"].mean()),2),
            "Highest Study Hours":round(float(summary["Total Hours"].max()),2),
            "Total Study Days":int(summary["Study Days"].sum())
        }

    def overall_student_activity(self,batch,section,roll):
        student=next((x for x in self.get_section_students(batch,section) if self._text(x.get("student_roll_number"))==self._text(roll)),None)
        if not student: return None,pd.DataFrame(),pd.DataFrame(),{}
        activity=self._activity_student("daily_activity_logs",batch,section,roll)
        sessions=[]
        daily=[]
        for item in activity.get("track",[]):
            parsed_date=self._date(item.get("date"))
            values=item.get("session",item.get("sessions",[]))
            if isinstance(values,dict): values=[values]
            day_seconds=0.0
            for index,session in enumerate(values,1):
                seconds=self.session_seconds(session,True)
                day_seconds+=seconds
                sessions.append({"Date":parsed_date.strftime("%d-%m-%Y") if parsed_date else "-","Day":parsed_date.strftime("%A") if parsed_date else "-","Session":index,"Start Time":self._time(session.get("start_time")),"End Time":self._time(session.get("end_time")),"Seconds":round(seconds,2),"Minutes":round(seconds/60,2),"Hours":round(seconds/3600,3)})
            if parsed_date and values:
                daily.append({"Date":parsed_date.strftime("%d-%m-%Y"),"Day":parsed_date.strftime("%A"),"Sessions":len(values),"Total Seconds":round(day_seconds,2),"Total Minutes":round(day_seconds/60,2),"Total Hours":round(day_seconds/3600,3)})
        sessions_df=pd.DataFrame(sessions)
        daily_df=pd.DataFrame(daily)
        total_seconds=float(sessions_df["Seconds"].sum()) if not sessions_df.empty else 0
        dates=[]
        for value in daily_df.get("Date",[]):
            try: dates.append(datetime.strptime(value,"%d-%m-%Y").date())
            except: pass
        today=date.today().strftime("%d-%m-%Y")
        metrics={
            "Total Study Hours":round(total_seconds/3600,2),
            "Total Study Minutes":round(total_seconds/60,2),
            "Total Sessions":len(sessions_df),
            "Study Days":len(daily_df),
            "Average Minutes / Day":round(total_seconds/60/len(daily_df),2) if len(daily_df) else 0,
            "Longest Session Minutes":round(float(sessions_df["Minutes"].max()),2) if not sessions_df.empty else 0,
            "Today's Study Minutes":round(float(daily_df.loc[daily_df["Date"]==today,"Total Minutes"].sum()),2) if not daily_df.empty else 0,
            "First Study Date":min(dates).strftime("%d-%m-%Y") if dates else "-",
            "Last Study Date":max(dates).strftime("%d-%m-%Y") if dates else "-"
        }
        return student,daily_df,sessions_df,metrics
