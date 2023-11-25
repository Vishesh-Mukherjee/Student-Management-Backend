from util import Field, prepare_response_dict
from sqlite3 import connect, Row
from service import ClassService, EnrollmentService, ProfileService
import logging
from fastapi import FastAPI
from constant import Message

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
    logger.info("Adding new student. Student name: %s %s", field.firstName, field.lastName)
    response = prepare_response_dict(student_profile_service.add_profile(field))
    logger.info("Student added successfully")
    return response

@app.put("/registrar/student")
def update_student(field: Field):
    logger.info("Updating student. Student ID: %s", field.id)
    response = prepare_response_dict(student_profile_service.update_profile(field))
    logger.info("Student updated sucessfully")
    return response

@app.get("/registrar/student/{id}")
def get_student(id: str):
    logger.info("Searching student. Student ID: %s", id)
    return prepare_response_dict(student_profile_service.get_profile(id))

@app.delete("/registrar/student/{id}")
def delete_student(id: str):
    logger.info("Deleting student. Student ID: %s", id)
    student_profile_service.delete_profile(id)
    logger.info(Message.STUDENT_DELETE_SUCCESSFULLY)
    return {"msg": Message.STUDENT_DELETE_SUCCESSFULLY}

@app.post("/registrar/instructor")
def add_student(field: Field):
    logger.info("Adding new instructor. Instructor name: %s %s", field)
    response = prepare_response_dict(instructor_profile_service.add_profile(field))
    logger.info("Instructor added successfully")
    return response

@app.put("/registrar/instructor")
def update_student(field: Field):
    logger.info("Updating instructor. Instructor ID: %s", field.id)
    response = prepare_response_dict(instructor_profile_service.update_profile(field))
    logger.info("Instructor updated successfully")
    return response

@app.get("/registrar/instructor/{id}")
def get_instructor(id: str):
    logger.info("Searching instructor. Instructor ID: %s", id)
    return prepare_response_dict(instructor_profile_service.get_profile(id))

@app.delete("/registrar/instructor/{id}")
def delete_student(id: str):
    logger.info("Deleting instructor. Instructor ID: %s", id)
    instructor_profile_service.delete_profile(id)
    logger.info(Message.INSTRUCTOR_DELETE_SUCCESSFULLY)
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