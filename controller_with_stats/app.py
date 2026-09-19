import streamlit as st
from streamlit_option_menu import option_menu
from utils.constants import Constants
from ui_pages.add_page import AddPage
from ui_pages.edit_page import EditPage
from ui_pages.delete_page import DeletePage
from ui_pages.view_page import ViewPage
from ui_pages.stats_page import StatsPage
import os
import sys

class ControllerApp:
    def __init__(self):
        st.set_page_config(page_title="Students Tracking System",page_icon="🎓",layout="wide")
    def sidebar(self):
        with st.sidebar:
            st.title("Controller")
            return option_menu("Students Tracking System",Constants.SIDEBAR_OPTIONS,icons=["plus-circle","pencil-square","trash","eye","bar-chart"],menu_icon="mortarboard",default_index=0)

    def render(self):
        selected=self.sidebar()
        if selected=="Add":
            AddPage().render()
        elif selected=="Edit":
            EditPage().render()
        elif selected=="Delete":
            DeletePage().render()
        elif selected=="View":
            ViewPage().render()
        elif selected=="Stats":
            StatsPage().render()

if __name__=="__main__":
    ControllerApp().render()