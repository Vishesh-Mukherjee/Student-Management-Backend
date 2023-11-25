from repository import ClassRepository, EnrollmentRepository, ProfileRepository
from util import DatabaseColumn, Field, get_find_class_dict, is_blank, valid_age
from sqlite3 import Connection, IntegrityError
from logging import Logger
from constant import DatabaseColumn, Message
from fastapi import HTTPException, status
from datetime import datetime


class ClassService:

    def __init__(self, conn: Connection, class_table_name: str, instructor_table_name: str, log: Logger):
        self._conn = conn
        self._log = log
        self._class_repository = ClassRepository(conn, class_table_name, log)
        self._instructor_repository = ProfileRepository(conn, instructor_table_name, log)

    def add_class(self, field: Field):
        if not self._instructor_repository.exists_by_attribute({DatabaseColumn.ID: field.instructorId}):
            self._log.info("Instructor does not exists. Instructor ID: %s", field.instructorId)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Instructor does not exists")
        class_data = get_find_class_dict(field)
        if self._class_repository.exists_by_attribute(class_data):
            self._log.info("Class already exists. Department: %s. Course Code: %s. Section Number %s", field.department, field.courseCode, field.sectionNumber)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class already exists")
        class_data[DatabaseColumn.INSTRUCTOR_ID] = field.instructorId
        class_data[DatabaseColumn.CLASS_NAME] = field.className
        class_data[DatabaseColumn.CURRENT_ENROLLMENT] = 0
        class_data[DatabaseColumn.MAX_ENROLLMENT] = field.maxEnrollment
        class_data[DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN] = field.automaticEnrollmentFrozen
        saved_class_data = self._class_repository.save(class_data)
        self._conn.commit()
        return saved_class_data
        
    def delete_class(self, id: str):
        id_dict = {DatabaseColumn.ID: id}
        if not self._class_repository.exists_by_attribute(id_dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.CLASS_DOES_NOT_EXISTS)
        self._class_repository.delete_by_attribute(id_dict)
        self._conn.commit()
        
    def update_instructor(self, id: str, instructor_id: str):
        class_data = self._class_repository.find_by_attribute({DatabaseColumn.ID: id})
        if class_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.CLASS_DOES_NOT_EXISTS)
        class_data[DatabaseColumn.INSTRUCTOR_ID] = instructor_id
        self._class_repository.save(class_data)
        self._conn.commit()
        
    def available_classes(self):
        return self._class_repository.findAllAvailableClasses()


class EnrollmentService:

    def __init__(self, conn: Connection, enrollment_table_name: str, class_table_name: str, log: Logger):
        self._conn = conn
        self._class_repository = ClassRepository(conn, class_table_name, log)
        self._enrollment_repository = EnrollmentRepository(conn, enrollment_table_name, log)

    def enroll(self, field: Field):
        class_data = self._class_repository.find_by_attribute(get_find_class_dict(field))
        if class_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.CLASS_DOES_NOT_EXISTS)
        if class_data[DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrollment has been frozen")
        if class_data[DatabaseColumn.CURRENT_ENROLLMENT] - class_data[DatabaseColumn.MAX_ENROLLMENT] >= 15:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiting list is full")
        if self._enrollment_repository.count_by_attribute({DatabaseColumn.STUDENT_ID: field.id, DatabaseColumn.WAITING_LIST: True}) >= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student cannot be in more than 3 waiting list")
        enrollment_data = {
            DatabaseColumn.STUDENT_ID: field.id,
            DatabaseColumn.CLASS_ID: class_data[DatabaseColumn.ID],
            DatabaseColumn.ENROLLED_ON: datetime.now(),
            DatabaseColumn.DROPPED: False,
        }
        enrollment_data[DatabaseColumn.WAITING_LIST] = False if class_data[DatabaseColumn.CURRENT_ENROLLMENT] < class_data[DatabaseColumn.MAX_ENROLLMENT] else True
        class_data[DatabaseColumn.CURRENT_ENROLLMENT] += 1
        try:
            self._enrollment_repository.save(enrollment_data)
            self._class_repository.save(class_data)
            self._conn.commit()
        except Exception:
            self._conn.rollback()

    def drop_enrollment(self, field: Field):
        class_data = self._get_class_data(field)
        enrollment_data = {
            DatabaseColumn.STUDENT_ID: field.id,
            DatabaseColumn.CLASS_ID: class_data[DatabaseColumn.ID],
            DatabaseColumn.DROPPED: False,
        }
        enrollment_data = self._enrollment_repository.find_by_attribute(enrollment_data)
        migrate_enrollment = None
        if enrollment_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not enrolled in this course")
        elif enrollment_data[DatabaseColumn.WAITING_LIST]:
            enrollment_data[DatabaseColumn.WAITING_LIST] = False
        elif class_data[DatabaseColumn.CURRENT_ENROLLMENT] > class_data[DatabaseColumn.MAX_ENROLLMENT] and not class_data[DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN]:
            search_enrollment = {
                DatabaseColumn.CLASS_ID: class_data[DatabaseColumn.ID],
                DatabaseColumn.DROPPED: False,
                DatabaseColumn.WAITING_LIST: True,
            }
            migrate_enrollment = self._enrollment_repository.find_by_attribute(search_enrollment, wild_card=f"ORDER BY {DatabaseColumn.ENROLLED_ON} ASC LIMIT 1")
            migrate_enrollment[DatabaseColumn.WAITING_LIST] = False
        enrollment_data[DatabaseColumn.DROPPED] = True
        class_data[DatabaseColumn.CURRENT_ENROLLMENT] -= 1
        try:
            self._enrollment_repository.save(enrollment_data)
            self._class_repository.save(class_data)
            if migrate_enrollment is not None:
                self._enrollment_repository.save(migrate_enrollment)
            self._conn.commit()
        except Exception:
            self._conn.rollback()

    def waiting_list_position(self, field: Field):
        class_data = self._get_class_data(field)
        position = self._enrollment_repository.waitingListPosition(class_data[DatabaseColumn.ID], field.id)
        if position is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not in waiting list")
        return position

    def class_enrollment(self, field: Field, on_waiting_list: bool):
        class_data = self._get_class_data(field)
        enrollment_data = {
            DatabaseColumn.CLASS_ID: class_data[DatabaseColumn.ID],
            DatabaseColumn.DROPPED: False,
            DatabaseColumn.WAITING_LIST: on_waiting_list,
        }
        return self._enrollment_repository.find_all_by_attribute(enrollment_data)

    def dropped_student(self, field: Field):
        class_data = self._get_class_data(field)
        enrollment_data = {
            DatabaseColumn.CLASS_ID: class_data[DatabaseColumn.ID],
            DatabaseColumn.DROPPED: True,
        }
        return self._enrollment_repository.find_all_by_attribute(enrollment_data)
    
    def _get_class_data(self, field: Field):
        class_data = self._class_repository.find_by_attribute(get_find_class_dict(field))
        if class_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.CLASS_DOES_NOT_EXISTS)
        return class_data
    

class ProfileService:

    def __init__(self, conn: Connection, table_name: str, log: Logger):
        self._conn = conn
        self._log = log
        self._profile_repository = ProfileRepository(conn, table_name, log)

    def add_profile(self, field: Field):
        student = self._validate_details(field)
        saved_student = self._profile_repository.save(student)
        self._conn.commit()
        return saved_student
    
    def get_profile(self, id: str):
        profile = self._profile_repository.find_by_attribute({DatabaseColumn.ID: id})
        if profile is None:
            self._log.error(Message.PROFLIE_NOT_FOUND)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.PROFLIE_NOT_FOUND)
        return profile

    def update_profile(self, field: Field):
        profile = self._profile_repository.find_by_attribute({DatabaseColumn.ID: field.id})
        if profile is None:
            self._log.error(Message.PROFLIE_NOT_FOUND)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.PROFLIE_NOT_FOUND)
        self._validate_details(field)
        profile[DatabaseColumn.ID] = field.id
        profile[DatabaseColumn.FIRST_NAME] = field.firstName
        profile[DatabaseColumn.LAST_NAME] = field.lastName
        profile[DatabaseColumn.AGE] = field.age
        saved_profile = self._profile_repository.save(profile)
        self._conn.commit()
        return saved_profile
    
    def delete_profile(self, id: str):
        profile_id_dict = {DatabaseColumn.ID: id}
        if not self._profile_repository.find_by_attribute(profile_id_dict):
            self._log.error(Message.PROFLIE_NOT_FOUND)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Message.PROFLIE_NOT_FOUND)
        self._profile_repository.delete_by_attribute(profile_id_dict)
        self._conn.commit()

    def _validate_details(self, field: Field):
        first_name = field.firstName
        last_name = field.lastName
        age = field.age
        invalid_details = []
        if is_blank(first_name):
            self._log.error("Invalid first name: %s", first_name)
            invalid_details.append("Firstname cannot be blank")
        if is_blank(last_name):
            self._log.error("Invalid last name: %s", last_name)
            invalid_details.append("Lastname cannot be blank")
        if not valid_age(age):
            self._log.error("Invalid age: %s", age)
            invalid_details.append("Age cannot be less than 1 or greater than 110")
        if len(invalid_details) != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=", ".join(invalid_details))
        return {
            DatabaseColumn.FIRST_NAME: first_name,
            DatabaseColumn.LAST_NAME: last_name,
            DatabaseColumn.AGE:  age,
        }