import streamlit as st
from pymongo import MongoClient
from config import Config

class MongoManager:
    @staticmethod
    @st.cache_resource
    def get_client():
        return MongoClient(st.secrets["DataBase"]["client"])

    @classmethod
    def get_department_db(cls,department):
        return cls.get_client()[department]

    @classmethod
    def get_assignment_db(cls,department):
        return cls.get_client()[f"{department}{Config.ASSIGNMENTS_SUFFIX}"]

    @classmethod
    def get_collection(cls,department,collection_name):
        return cls.get_department_db(department)[collection_name]

    @classmethod
    def get_assignment_collection(cls,department,collection_name):
        return cls.get_assignment_db(department)[collection_name]

    @classmethod
    def collection_exists(cls,department,collection_name):
        return collection_name in cls.get_department_db(department).list_collection_names()

    @classmethod
    def assignment_collection_exists(cls,department,collection_name):
        return collection_name in cls.get_assignment_db(department).list_collection_names()