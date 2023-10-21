from repository import *
from util import *
from sqlite3 import Connection, IntegrityError
from logging import Logger
from constant import Constant
from fastapi import HTTPException, status
from datetime import datetime


class ClassService:

    def __init__(self, conn: Connection, logger: Logger):
        self._conn = conn
        self._classRepository = ClassRepository(conn, "class", logger)

    def addClass(self, field: Field):
        classData = getFindClassDict(field)
        if self._classRepository.existsByAttribute(classData):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class already exists")
        classData[Constant.INSTRUCTOR_ID] = field.instructorId
        classData[Constant.CLASS_NAME] = field.className
        classData[Constant.CURRENT_ENROLLMENT] = 0
        classData[Constant.MAX_ENROLLMENT] = field.maxEnrollment
        classData[Constant.AUTOMATIC_ENROLLMENT_FROZEN] = field.automaticEnrollmentFrozen
        try:
            self._classRepository.save(classData)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def removeSection(self, field: Field):
        classData = getFindClassDict(field)
        if not self._classRepository.existsByAttribute(classData):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class does not exists")
        try:
            self._classRepository.deleteByAttribute(classData)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def updateInstructor(self, field: Field):
        classData = self._classRepository.findByAttribute(getFindClassDict(field))
        if classData is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class does not exists")
        classData[Constant.INSTRUCTOR_ID] = field.instructorId
        try:
            self._classRepository.save(classData)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})
        
    def availableClasses(self):
        return self._classRepository.findAllAvailableClasses()


class EnrollmentService:

    def __init__(self, conn: Connection, logger: Logger):
        self._conn = conn
        self._classRepository = ClassRepository(conn, "class", logger)
        self._enrollmentRepository = EnrollmentRepository(conn, "enrollment", logger)

    def enroll(self, field: Field):
        classData = self._classRepository.findByAttribute(getFindClassDict(field))
        if classData is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class does not exists")
        if classData[Constant.AUTOMATIC_ENROLLMENT_FROZEN]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrollment has been frozen")
        if classData[Constant.CURRENT_ENROLLMENT] - classData[Constant.MAX_ENROLLMENT] >= 15:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiting list is full")
        if self._enrollmentRepository.countByAttribute({Constant.STUDENT_ID: field.studentId, Constant.WAITING_LIST: True}) >= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student cannot be in more than 3 waiting list")
        enrollmentData = {
            Constant.STUDENT_ID: field.studentId,
            Constant.CLASS_ID: classData[Constant.ID],
            Constant.ENROLLED_ON: datetime.now(),
            Constant.DROPPED: False,
        }
        enrollmentData[Constant.WAITING_LIST] = False if classData[Constant.CURRENT_ENROLLMENT] < classData[Constant.MAX_ENROLLMENT] else True
        classData[Constant.CURRENT_ENROLLMENT] += 1
        try:
            self._enrollmentRepository.save(enrollmentData)
            self._classRepository.save(classData)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})

    def dropEnrollment(self, field: Field):
        classData = self._getClassData(field)
        enrollmentData = {
            Constant.STUDENT_ID: field.studentId,
            Constant.CLASS_ID: classData[Constant.ID],
            Constant.DROPPED: False,
        }
        enrollmentData = self._enrollmentRepository.findByAttribute(enrollmentData)
        migrateEnrollment = None
        if enrollmentData is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not enrolled in this course")
        elif enrollmentData[Constant.WAITING_LIST]:
            enrollmentData[Constant.WAITING_LIST] = False
        elif classData[Constant.CURRENT_ENROLLMENT] > classData[Constant.MAX_ENROLLMENT] and not classData[Constant.AUTOMATIC_ENROLLMENT_FROZEN]:
            searchEnrollment = {
                Constant.CLASS_ID: classData[Constant.ID],
                Constant.DROPPED: False,
                Constant.WAITING_LIST: True,
            }
            migrateEnrollment = self._enrollmentRepository.findByAttribute(searchEnrollment, wildCard=f"ORDER BY {Constant.ENROLLED_ON} ASC LIMIT 1")
            migrateEnrollment[Constant.WAITING_LIST] = False
        enrollmentData[Constant.DROPPED] = True
        classData[Constant.CURRENT_ENROLLMENT] -= 1
        try:
            self._enrollmentRepository.save(enrollmentData)
            self._classRepository.save(classData)
            if migrateEnrollment is not None:
                self._enrollmentRepository.save(migrateEnrollment)
            self._conn.commit()
        except IntegrityError as e:
            self._conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"type": type(e).__name__, "msg": str(e)})

    def waitingListPosition(self, field: Field):
        classData = self._getClassData(field)
        position = self._enrollmentRepository.waitingListPosition(classData[Constant.ID], field.studentId)
        if position is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not in waiting list")
        return position

    def classEnrollment(self, field: Field, onWaitingList: bool):
        classData = self._getClassData(field)
        enrollmentData = {
            Constant.CLASS_ID: classData[Constant.ID],
            Constant.DROPPED: False,
            Constant.WAITING_LIST: onWaitingList,
        }
        return self._enrollmentRepository.findAllByAttribute(enrollmentData)

    def droppedStudent(self, field: Field):
        classData = self._getClassData(field)
        enrollmentData = {
            Constant.CLASS_ID: classData[Constant.ID],
            Constant.DROPPED: True,
        }
        return self._enrollmentRepository.findAllByAttribute(enrollmentData)
    
    def _getClassData(self, field: Field):
        classData = self._classRepository.findByAttribute(getFindClassDict(field))
        if classData is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class does not exists")
        return classData
