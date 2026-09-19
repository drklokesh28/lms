import streamlit as st

class StateManager:
    @staticmethod
    def set(key,value):
        st.session_state[key]=value

    @staticmethod
    def get(key,default=None):
        return st.session_state.get(key,default)

    @staticmethod
    def exists(key):
        return key in st.session_state

    @staticmethod
    def delete(key):
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def toggle(key,default=False):
        if key not in st.session_state:
            st.session_state[key]=default
        return st.session_state[key]

    @staticmethod
    def save_dataframe(key,dataframe):
        st.session_state[key]=dataframe.copy()

    @staticmethod
    def get_dataframe(key):
        return st.session_state.get(key)

    @staticmethod
    def clear_prefix(prefix):
        keys=[key for key in st.session_state if key.startswith(prefix)]
        for key in keys:
            del st.session_state[key]

    @staticmethod
    def reset(keys):
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]