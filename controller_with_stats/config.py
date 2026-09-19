class Config:
    DEPARTMENTS=["AI_DS","DS","CSE","CAI"]
    SUBJECT_TYPES=["Theory","Lab","Skill-Enhancement","Others"]
    BATCHES=["2023-2027","2024-2028","2025-2029","2026-2030"]

    STUDENTS_COLLECTION="students_list"
    COURSES_COLLECTION="courses"
    MATERIALS_COLLECTION="materials"
    CURRICULUM_COLLECTION="course_curriculum"
    ASSIGNMENTS_SUFFIX="_assignments"

    STUDENT_COLUMNS=["Student Name","Semister","Roll Number","Batch","Gender","Section","Password"]
    SUBJECT_COLUMNS=["semister","subject_name","subject_credits","subject_type","alloted_faculty_ids","alloted_sections"]
    CURRICULUM_COLUMNS=["unit_number","topic_name","yt_url","description"]
    TASK_COLUMNS=["question_name","option_a","option_b","option_c","option_d","correct_option","marks"]