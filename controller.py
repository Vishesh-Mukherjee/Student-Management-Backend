from util import Field, prepare_response_dict
from sqlite3 import connect, Row
from service import ClassService, EnrollmentService, ProfileService
import logging
from fastapi import FastAPI

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

conn = connect("database.db", check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = Row

class_service = ClassService(conn, "class", logger)
enrollment_service = EnrollmentService(conn, "enrollment", logger)
student_profile_service = ProfileService(conn, "student", logger)
instructor_profile_service = ProfileService(conn, "instructor", logger)

app = FastAPI()

@app.post("/registrar/student")
def add_student(field: Field):
    return prepare_response_dict(student_profile_service.add_profile(field))

@app.put("/registrar/student")
def update_student(field: Field):
    return prepare_response_dict(student_profile_service.update_profile(field))

@app.get("/registrar/student/{id}")
def update_student(field: Field, id: str):
    return prepare_response_dict(student_profile_service.get_profile(id))

@app.delete("/registrar/student/{id}")
def delete_student(id: str):
    student_profile_service.delete_profile(id)
    return {"msg": "Student deleted successfully"}

@app.post("/registrar/instructor")
def add_student(field: Field):
    return prepare_response_dict(instructor_profile_service.add_profile(field))

@app.put("/registrar/instructor")
def update_student(field: Field):
    return prepare_response_dict(instructor_profile_service.update_profile(field))

@app.get("/registrar/instructor/{id}")
def update_student(field: Field, id: str):
    return prepare_response_dict(instructor_profile_service.get_profile(id))

@app.delete("/registrar/instructor/{id}")
def delete_student(id: str):
    instructor_profile_service.delete_profile(id)
    return {"msg": "Instructor deleted successfully"}

@app.post("/registrar/instructor")
def add_student(field: Field):
    return prepare_response_dict(student_profile_service.add_profile(field))

@app.put("/registrar/instructor")
def update_student(field: Field):
    return prepare_response_dict(student_profile_service.update_profile(field))

@app.get("/registrar/instructor/{id}")
def update_student(field: Field, id: str):
    return prepare_response_dict(student_profile_service.get_profile(id))

@app.delete("/registrar/instructor/{id}")
def delete_student(id: str):
    student_profile_service.delete_profile(id)
    return {"msg": "Instructor deleted successfully"}

@app.post("/registrar/class")
def add_class(field: Field):
    return prepare_response_dict(class_service.add_class(field))

@app.delete("/registrar/class")
def remove_section(field: Field):
    class_service.remove_section(field)
    return {"msg": "Class deleted successfully"}

@app.put("/registrar/class")
def update_instructor(field: Field):
    class_service.update_instructor(field)
    return {"msg": "Instructor updated successfully"}


@app.get("/student/class")
def available_classes():
    return class_service.available_classes()

@app.post("/student/class")
def enroll(field: Field):
    enrollment_service.enroll(field)
    return {"msg": "Enrolled successfully"}

@app.delete("/student/class")
def drop_enrollment(field: Field):
    enrollment_service.drop_enrollment(field)
    return {"msg": "Enrollment dropped successfully"}

@app.get("/student/class/waitinglist")
def waitinglist_position(field: Field):
    position = enrollment_service.waiting_list_position(field)
    return {"msg": f"Current position in waiting list: {position}"}


@app.get("/instructor/waitinglist")
def waiting_list(field: Field):
    return enrollment_service.class_enrollment(field, True)

@app.get("/instructor/class")
def current_enrollment(field: Field):
    return enrollment_service.class_enrollment(field, False) 

@app.get("/instructor/class/dropped")
def dropped_student(field: Field):
    return enrollment_service.dropped_student(field)

@app.delete("/instructor/class")
def drop_student(field: Field):
    enrollment_service.drop_enrollment(field)
    return {"msg": "Student dropped successfully"}