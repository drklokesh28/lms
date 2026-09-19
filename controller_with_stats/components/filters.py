import streamlit as st
from config import Config

class Filters:
    @staticmethod
    def department(key="department"):
        return st.pills("Select Department",Config.DEPARTMENTS,key=key,wrap=True)

    @staticmethod
    def batch(options=None,key="batch"):
        options=options or Config.BATCHES
        return st.selectbox("Select Batch",options,key=key)

    @staticmethod
    def semester(options,key="semester"):
        return st.selectbox("Select Semester",options,key=key)

    @staticmethod
    def subject(options,key="subject"):
        return st.selectbox("Select Subject",options,key=key)

    @staticmethod
    def subject_type(options,key="subject_type"):
        return st.selectbox("Select Subject Type",options,key=key)

    @staticmethod
    def faculty_id(key="faculty_id"):
        return st.number_input("Enter Faculty ID",min_value=1,step=1,key=key)

    @staticmethod
    def sections(options,key="sections"):
        return st.multiselect("Select Sections",options,key=key)

    @staticmethod
    def task(options,key="task"):
        return st.selectbox("Select Task",options,key=key)

    @staticmethod
    def file_uploader(label,file_type="csv",key=None):
        return st.file_uploader(label,type=[file_type],key=key)

    @staticmethod
    def keep_visible(key):
        return st.toggle("Keep Data Visible",value=True,key=key)