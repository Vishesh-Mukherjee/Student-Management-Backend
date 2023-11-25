from util import Field, prepare_response_dict
from sqlite3 import connect, Row
from service import ClassService, EnrollmentService, ProfileService
import logging
from fastapi import FastAPI
from constant import Message, DatabaseColumn

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

conn = connect("database.db", check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = Row

class_service = ClassService(conn, "class", "instructor", log)
enrollment_service = EnrollmentService(conn, "enrollment", "class", log)
student_profile_service = ProfileService(conn, "student", log)
instructor_profile_service = ProfileService(conn, "instructor", log)

app = FastAPI()

@app.post("/registrar/student")
def add_student(field: Field):
    log.info("Adding new student. Student name: %s %s", field.firstName, field.lastName)
    response_dict = student_profile_service.add_profile(field)
    log.info("Student added successfully. Student ID: %s", response_dict[DatabaseColumn.ID])
    return prepare_response_dict(response_dict)

@app.put("/registrar/student")
def update_student(field: Field):
    log.info("Updating student. Student ID: %s", field.id)
    response = prepare_response_dict(student_profile_service.update_profile(field))
    log.info("Student updated sucessfully")
    return response

@app.get("/registrar/student/{id}")
def get_student(id: str):
    log.info("Searching student. Student ID: %s", id)
    return prepare_response_dict(student_profile_service.get_profile(id))

@app.delete("/registrar/student/{id}")
def delete_student(id: str):
    log.info("Deleting student. Student ID: %s", id)
    student_profile_service.delete_profile(id)
    log.info(Message.STUDENT_DELETE_SUCCESSFULLY)
    return {"msg": Message.STUDENT_DELETE_SUCCESSFULLY}

@app.post("/registrar/instructor")
def add_student(field: Field):
    log.info("Adding new instructor. Instructor name: %s %s", field.firstName, field.lastName)
    response_dict = instructor_profile_service.add_profile(field)
    log.info("Instructor added successfully. Instructor ID: %s", response_dict[DatabaseColumn.ID])
    return prepare_response_dict(response_dict)

@app.put("/registrar/instructor")
def update_student(field: Field):
    log.info("Updating instructor. Instructor ID: %s", field.id)
    response = prepare_response_dict(instructor_profile_service.update_profile(field))
    log.info("Instructor updated successfully")
    return response

@app.get("/registrar/instructor/{id}")
def get_instructor(id: str):
    log.info("Searching instructor. Instructor ID: %s", id)
    return prepare_response_dict(instructor_profile_service.get_profile(id))

@app.delete("/registrar/instructor/{id}")
def delete_student(id: str):
    log.info("Deleting instructor. Instructor ID: %s", id)
    instructor_profile_service.delete_profile(id)
    log.info(Message.INSTRUCTOR_DELETE_SUCCESSFULLY)
    return {"msg": "Instructor deleted successfully"}

@app.post("/registrar/class")
def add_class(field: Field):
    log.info("Adding new class")
    response_dict = class_service.add_class(field)
    log.info("Class added successfully. Class ID: %s", response_dict[DatabaseColumn.ID])
    return prepare_response_dict(response_dict)

@app.delete("/registrar/class/{id}")
def delete_class(id: str):
    log.info("Deleting class. Class ID: %s", id)
    class_service.delete_class(id)
    log.info("Class delete sucessfully")
    return {"msg": "Class deleted successfully"}

@app.put("/registrar/class/{id}/{instructor_id}")
def update_instructor(id: str, instructor_id: str):
    log.info("Updating class instructor. Class Id: %s. Instructor ID: %s", id, instructor_id)
    class_service.update_instructor(id, instructor_id)
    log.info(Message.CLASS_INSTRUCTOR_UPDATED_SUCCESSFULLY)
    return {"msg": Message.CLASS_INSTRUCTOR_UPDATED_SUCCESSFULLY}


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