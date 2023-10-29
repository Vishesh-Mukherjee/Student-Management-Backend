from unittest import TestCase
from sqlite3 import connect, Row
from service import ProfileService
from constant import DatabaseColumn, Query
from util import Field, insert_test_data
import logging

class TestProfileService(TestCase):

    @classmethod
    def setUp(cls):
        logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG)
        conn = connect("database.db", check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = Row
        insert_test_data(conn)
        cls._initCount = conn.execute(Query.STUDENT_COUNT).fetchone()[0]
        cls._conn = conn
        cls._student_service = ProfileService(conn, "student", logger)

    @classmethod
    def tearDown(cls):
        cls._conn.close()

    def test_add_student(self):
        field = Field()
        field.firstName = "Gault"
        field.lastName = "Graply"
        field.age = 19
        self._student_service.add_profile(field)
        count = self._conn.execute(Query.STUDENT_COUNT).fetchone()[0]
        self.assertEqual(count, self._initCount+1)

    def test_update_student(self):
        field = Field()
        student_id = "6f68124d-4494-4a61-bd52-dc3b313c6ab7"
        field.id = student_id
        field.firstName = "Gault"
        field.lastName = "Graply"
        field.age = 19
        self._student_service.update_profile(field)
        count = self._conn.execute(Query.STUDENT_COUNT).fetchone()[0]
        student = self._student_service.get_profile(student_id)
        self.assertEqual(count, self._initCount)
        self.assertEqual(student[DatabaseColumn.FIRST_NAME], field.firstName)
        self.assertEqual(student[DatabaseColumn.LAST_NAME], field.lastName)
        self.assertEqual(student[DatabaseColumn.AGE], field.age)

    def test_get_student(self):
        student_id = "6f68124d-4494-4a61-bd52-dc3b313c6ab7"
        expected = {
            DatabaseColumn.ID: student_id,
            DatabaseColumn.FIRST_NAME: "Foo",
            DatabaseColumn.LAST_NAME: "Bar",
            DatabaseColumn.AGE: 19,
        }
        actual = self._student_service.get_profile(student_id)
        self.assertEqual(actual, expected)

    def test_delete_student(self):
        student_id = "6f68124d-4494-4a61-bd52-dc3b313c6ab7"
        self._student_service.delete_profile(student_id)
        count = self._conn.execute(Query.STUDENT_COUNT).fetchone()[0]
        self.assertEqual(count, self._initCount-1)
