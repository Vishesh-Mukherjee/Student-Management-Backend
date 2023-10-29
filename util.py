from pydantic import BaseModel
from constant import DatabaseColumn
from sqlite3 import connect

class Field(BaseModel):
    instructorId: str = None
    department: str = None
    courseCode: str  = None
    sectionNumber: int = 1
    className: str = None
    maxEnrollment: int = 20
    automaticEnrollmentFrozen: bool = False
    id: str = None
    firstName: str = None
    lastName: str = None
    age: int= None

def get_find_class_dict(field: Field):
    return {
        DatabaseColumn.DEPARTMENT: field.department,
        DatabaseColumn.COURSE_CODE: field.courseCode,
        DatabaseColumn.SECTION_NUMBER: field.sectionNumber,
    }

def prepare_response_dict(data: dict):
    converted_data = {}
    for key in data.keys():
        converted_data[snake_to_camel(key)] = data[key]
    return converted_data

def snake_to_camel(key: str):
    converted_str = ""
    to_upper_case = False
    for c in key:
        if c != "_":
            if to_upper_case:
                converted_str += c.upper()
                to_upper_case = False
            else:
                converted_str += c
        else:
            to_upper_case = True
    return converted_str

def is_blank(data: str):
    if data is None:
        return True
    for c in data:
        if c != " ":
            return False
    return True

def valid_age(age: int):
    if age is None or age < 1 or age > 110:
        return False
    return True

def insert_test_data(conn: connect):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO class ('id', instructor_id, department, course_code, section_number, class_name, current_enrollment, max_enrollment, automatic_enrollment_frozen) VALUES
            ('c25ccf22-4539-4810-b78b-81049b546bf1', 'INS101', 'FOO', 'BAR', 1, 'BAZ', 0, 10, true),
            ('9cfaf63d-77db-4d7e-b72b-2a1d2fd1b57a', 'INS102', 'QUX', 'QUUX', 1, 'CORGE', 0, 10, false),
            ('01d2cdbc-abe3-4ca2-bb15-7b9c38aff57b', 'INS103', 'GRAULT', 'GRAPLY', 1, 'WALDO', 0, 15, true);
    ''')

    cursor.execute('''
        INSERT INTO student (id, first_name, last_name, age) VALUES
            ('6f68124d-4494-4a61-bd52-dc3b313c6ab7', 'Foo', 'Bar', 19),
            ('52e9c54c-1880-4920-a322-ca7a7bc3c8c7', 'Baz', 'Qux', 20),
            ('41359222-8d72-4dd7-a697-91bd5146aa58', 'Quux', 'Corge', 20);
    ''')
    conn.commit()

def clear_tables(conn: connect):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM class')
    cursor.execute('DELETE FROM student')
    conn.commit()