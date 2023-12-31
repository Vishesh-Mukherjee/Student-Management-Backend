class DatabaseColumn:
    ID = "id"
    INSTRUCTOR_ID = "instructor_id"
    DEPARTMENT = "department"
    COURSE_CODE = "course_code"
    SECTION_NUMBER = "section_number"
    CLASS_NAME = "class_name"
    CURRENT_ENROLLMENT = "current_enrollment"
    MAX_ENROLLMENT = "max_enrollment"
    AUTOMATIC_ENROLLMENT_FROZEN = "automatic_enrollment_frozen"

    STUDENT_ID = "student_id"
    ENROLLED_ON = "enrolled_on"
    DROPPED = "dropped"
    WAITING_LIST = "waiting_list"
    CLASS_ID = "class_id"

    AND = "AND"
    OR = "OR"

    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    AGE = "age"

class Message:
    CLASS_DOES_NOT_EXISTS = "Class does not exists"
    PROFLIE_NOT_FOUND = "Profile not found"
    STUDENT_DELETE_SUCCESSFULLY = "Student delete successfully"
    INSTRUCTOR_DELETE_SUCCESSFULLY = "Instructor delete successfully"
    CLASS_INSTRUCTOR_UPDATED_SUCCESSFULLY = "Class instructor updated successfully"

class Query:
    STUDENT_COUNT = "SELECT COUNT(*) FROM student"
    CLASS_COUNT = "SELECT COUNT(*) FROM class"