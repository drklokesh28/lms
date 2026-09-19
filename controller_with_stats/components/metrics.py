import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

class Metrics:
    @staticmethod
    def show(title,value,delta=None):
        st.metric(title,value,delta)

    @classmethod
    def student_import(cls,result):
        col1,col2,col3,col4=st.columns(4)
        with col1:
            cls.show("Total Students",result.get("total",0))
        with col2:
            cls.show("Inserted",result.get("inserted",0))
        with col3:
            cls.show("Updated",result.get("updated",0))
        with col4:
            cls.show("Already Existing",result.get("already_existing",0))
        style_metric_cards()

    @classmethod
    def course_import(cls,result):
        col1,col2,col3,col4=st.columns(4)
        with col1:
            cls.show("Total Subjects",result.get("total",0))
        with col2:
            cls.show("Inserted",result.get("inserted",0))
        with col3:
            cls.show("Updated",result.get("updated",0))
        with col4:
            cls.show("Existing",result.get("already_existing",0))
        style_metric_cards()

    @classmethod
    def import_summary(cls,result):
        col1,col2,col3,col4=st.columns(4)
        with col1:
            cls.show("Uploaded",result.get("uploaded",0))
        with col2:
            cls.show("Valid",result.get("valid",0))
        with col3:
            cls.show("Invalid",result.get("invalid",0))
        with col4:
            cls.show("Inserted",result.get("inserted",0))
        style_metric_cards()