from repository import ClassRepository, EnrollmentRepository, ProfileRepository
from util import DatabaseColumn, Field, get_find_class_dict, is_blank, valid_age
from sqlite3 import Connection, IntegrityError
from logging import Logger
from constant import DatabaseColumn, Error
from fastapi import HTTPException, status
from datetime import datetime


class ClassService:

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        self._conn = conn
        self._class_repository = ClassRepository(conn, table_name, logger)

    def add_class(self, field: Field):
        class_data = get_find_class_dict(field)
        if self._class_repository.exists_by_attribute(class_data):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class already exists")
        class_data[DatabaseColumn.INSTRUCTOR_ID] = field.instructorId
        class_data[DatabaseColumn.CLASS_NAME] = field.className
        class_data[DatabaseColumn.CURRENT_ENROLLMENT] = 0
        class_data[DatabaseColumn.MAX_ENROLLMENT] = field.maxEnrollment
        class_data[DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN] = field.automaticEnrollmentFrozen
        try:
            saved_class_data = self._class_repository.save(class_data)
            self._conn.commit()
            return saved_class_data
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def remove_section(self, field: Field):
        class_data = get_find_class_dict(field)
        if not self._class_repository.exists_by_attribute(class_data):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Error.CLASS_DOES_NOT_EXISTS)
        try:
            self._class_repository.delete_by_attribute(class_data)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def update_instructor(self, field: Field):
        class_data = self._class_repository.find_by_attribute(get_find_class_dict(field))
        if class_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Error.CLASS_DOES_NOT_EXISTS)
        class_data[DatabaseColumn.INSTRUCTOR_ID] = field.instructorId
        try:
            self._class_repository.save(class_data)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def available_classes(self):
        return self._class_repository.findAllAvailableClasses()


class EnrollmentService:

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        self._conn = conn
        self._class_repository = ClassRepository(conn, table_name, logger)
        self._enrollment_repository = EnrollmentRepository(conn, "enrollment", logger)

    def enroll(self, field: Field):
        class_data = self._class_repository.find_by_attribute(get_find_class_dict(field))
        if class_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Error.CLASS_DOES_NOT_EXISTS)
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
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})

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
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=Error.CLASS_DOES_NOT_EXISTS)
        return class_data
    

class ProfileService:

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        self._conn = conn
        self._profile_repository = ProfileRepository(conn, table_name, logger)

    def add_profile(self, field: Field):
        student = self._validate_details(field)
        saved_student = self._profile_repository.save(student)
        self._conn.commit()
        return saved_student
    
    def get_profile(self, id: str):
        return self._profile_repository.find_by_attribute({DatabaseColumn.ID: id})

    def update_profile(self, field: Field):
        profile = self._profile_repository.find_by_attribute({DatabaseColumn.ID: field.id})
        if profile is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found")
        self._validate_details(field)
        profile[DatabaseColumn.ID] = field.id
        if field.firstName is not None:
            profile[DatabaseColumn.FIRST_NAME] = field.firstName
        if field.lastName is not None:
            profile[DatabaseColumn.LAST_NAME] = field.lastName
        if field.age is not None:
            profile[DatabaseColumn.AGE] = field.age
        saved_profile = self._profile_repository.save(profile)
        self._conn.commit()
        return saved_profile
    
    def delete_profile(self, id: str):
        profile_id_dict = {DatabaseColumn.ID: id}
        if not self._profile_repository.find_by_attribute(profile_id_dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found")
        try:
            self._profile_repository.delete_by_attribute(profile_id_dict)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})

    def _validate_details(self, field: Field):
        first_name = field.firstName
        last_name = field.lastName
        age = field.age
        invalid_details = []
        if is_blank(first_name):
            invalid_details.append("Firstname cannot be blank")
        if is_blank(last_name):
            invalid_details.append("Lastname cannot be blank")
        if not valid_age(age):
            invalid_details.append("Age cannot be less than 1 or greater than 110")
        if len(invalid_details) != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=", ".join(invalid_details))
        return {
            DatabaseColumn.FIRST_NAME: first_name,
            DatabaseColumn.LAST_NAME: last_name,
            DatabaseColumn.AGE:  age,
        }