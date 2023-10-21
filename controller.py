from util import *
from sqlite3 import connect, Row
from service import *
import logging
from fastapi import FastAPI

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

conn = connect("database.db", check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = Row

classService = ClassService(conn, logger)
enrollmentService = EnrollmentService(conn, logger)

app = FastAPI()

@app.post("/registrar")
def add_class(field: Field):
    classService.addClass(field)
    return {"msg": "Class added successfully"}

@app.delete("/registrar")
def remove_section(field: Field):
    classService.removeSection(field)
    return {"msg": "Class deleted successfully"}

@app.put("/registrar")
def update_instructor(field: Field):
    classService.updateInstructor(field)
    return {"msg": "Instructor updated successfully"}

@app.get("/student")
def available_classes():
    return classService.availableClasses()

@app.post("/student")
def enroll(field: Field):
    enrollmentService.enroll(field)
    return {"msg": "Enrolled successfully"}

@app.delete("/student")
def drop_enrollment(field: Field):
    enrollmentService.dropEnrollment(field)
    return {"msg": "Enrollment dropped successfully"}

@app.get("/student/waitinglist")
def waitinglist_position(field: Field):
    position = enrollmentService.waitingListPosition(field)
    return {"msg": f"Current position in waiting list: {position}"}

@app.get("/instructor/waitinglist")
def waiting_list(field: Field):
    return enrollmentService.classEnrollment(field, True)

@app.get("/instructor")
def current_waiting_list(field: Field):
    return enrollmentService.classEnrollment(field, False) 

@app.get("/instructor/dropped")
def dropped_student(field: Field):
    return enrollmentService.droppedStudent(field)

@app.delete("/instructor/drop")
def drop_student(field: Field):
    enrollmentService.dropEnrollment(field)
    return {"msg": "Student dropped successfully"}
