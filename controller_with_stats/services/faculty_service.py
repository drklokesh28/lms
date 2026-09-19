from repositories.course_repository import CourseRepository

class FacultyService:
    def __init__(self,department):
        self.repository=CourseRepository(department)

    def get_courses(self,faculty_id,batch=None):
        courses=self.repository.get_by_faculty_batch(faculty_id,batch) if batch else self.repository.get_by_faculty(faculty_id)
        return courses

    def get_semesters(self,faculty_id,batch=None):
        courses=self.get_courses(faculty_id,batch)
        return sorted(set(course["semester"] for course in courses))

    def get_subjects(self,faculty_id,batch,semester):
        courses=self.get_courses(faculty_id,batch)
        return sorted(set(course["subject_name"] for course in courses if course["semester"]==int(semester)))

    def get_subject_types(self,faculty_id,batch,semester,subject_name):
        courses=self.get_courses(faculty_id,batch)
        return sorted(set(course["subject_type"] for course in courses if course["semester"]==int(semester) and course["subject_name"]==subject_name))

    def get_course(self,faculty_id,batch,semester,subject_name):
        courses=self.get_courses(faculty_id,batch)
        for course in courses:
            if course["semester"]==int(semester) and course["subject_name"]==subject_name:
                return course
        return None

    def get_sections(self,faculty_id,batch,semester,subject_name):
        course=self.get_course(faculty_id,batch,semester,subject_name)
        if not course:
            return []
        faculty_ids=course.get("allotted_faculty_ids",[])
        sections=course.get("allotted_sections",[])
        return [section for faculty,section in zip(faculty_ids,sections) if int(faculty)==int(faculty_id)]

    def is_authorized(self,faculty_id,batch,semester,subject_name,section=None):
        sections=self.get_sections(faculty_id,batch,semester,subject_name)
        if section is None:
            return bool(sections)
        return section in sections