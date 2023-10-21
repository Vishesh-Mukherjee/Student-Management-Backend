from pydantic import BaseModel
from constant import Constant

class Field(BaseModel):
    instructorId: str = None
    department: str = None
    courseCode: str  = None
    sectionNumber: int = None
    className: str = None
    maxEnrollment: int = None
    automaticEnrollmentFrozen: bool = None
    studentId: str = None

def getFindClassDict(field: Field):
    return {
        Constant.DEPARTMENT: field.department,
        Constant.COURSE_CODE: field.courseCode,
        Constant.SECTION_NUMBER: field.sectionNumber,
    }