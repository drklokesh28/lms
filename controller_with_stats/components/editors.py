import streamlit as st
import pandas as pd

class Editors:
    @staticmethod
    def dataframe(dataframe,key,num_rows="dynamic",disabled=False):
        dataframe=dataframe if isinstance(dataframe,pd.DataFrame) else pd.DataFrame(dataframe)
        return st.data_editor(dataframe,use_container_width=True,num_rows=num_rows,disabled=disabled,key=key)

    @staticmethod
    def table(dataframe):
        dataframe=dataframe if isinstance(dataframe,pd.DataFrame) else pd.DataFrame(dataframe)
        st.dataframe(dataframe,use_container_width=True)

    @staticmethod
    def json(data):
        st.json(data)

    @staticmethod
    def paths(key,value=""):
        return st.text_area("Enter Material Paths",value=value,placeholder="./books/book1.pdf, ./books/book2.pdf",key=key)

    @staticmethod
    def task_name(key,value=""):
        return st.text_input("Task Name",value=value,key=key)

    @staticmethod
    def confirm_delete(key):
        return st.checkbox("I confirm permanent deletion",key=key)