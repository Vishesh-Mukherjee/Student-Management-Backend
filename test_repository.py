from unittest import TestCase
from repository import ClassRepository
from sqlite3 import connect, Row
from util import DatabaseColumn, insert_test_data, clear_tables
from constant import Query
import logging


class TestClassRepository(TestCase):

    @classmethod
    def setUp(cls):
        logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG)
        conn = connect("database.db", check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        clear_tables(conn)
        insert_test_data(conn)
        cls._init_count = conn.execute(Query.CLASS_COUNT).fetchone()[0]
        conn.row_factory = Row

        cls._conn = conn
        cls._class_repository = ClassRepository(conn, "class", logger)

    @classmethod
    def tearDown(cls):
        clear_tables(cls._conn)
        cls._conn.close()

    def test_save(self):
        class_data = {
            DatabaseColumn.INSTRUCTOR_ID: "INS",
            DatabaseColumn.DEPARTMENT: "DEP",
            DatabaseColumn.COURSE_CODE: "COR",
            DatabaseColumn.SECTION_NUMBER: 1,
            DatabaseColumn.CLASS_NAME: "CLA",
            DatabaseColumn.CURRENT_ENROLLMENT: 0,
            DatabaseColumn.MAX_ENROLLMENT: 10,
            DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: True,
        }
        self._class_repository.save(class_data)
        self.assertEqual(self._class_repository.count_by_attribute(), self._init_count+1)

    def test_save_update(self):
        class_id_dict = {
            DatabaseColumn.ID: "c25ccf22-4539-4810-b78b-81049b546bf1"
        }
        class_data = {
            DatabaseColumn.INSTRUCTOR_ID: "INS",
            DatabaseColumn.DEPARTMENT: "DEP",
            DatabaseColumn.COURSE_CODE: "COR",
            DatabaseColumn.SECTION_NUMBER: 1,
            DatabaseColumn.CLASS_NAME: "CLA",
            DatabaseColumn.CURRENT_ENROLLMENT: 0,
            DatabaseColumn.MAX_ENROLLMENT: 10,
            DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: False
        } | class_id_dict
        self._class_repository.save(class_data)
        self.assertEqual(self._class_repository.count_by_attribute(), self._init_count)
        self.assertEqual(self._class_repository.find_by_attribute(class_id_dict), class_data)

    def test_save_all(self):
        class_data = [
            {
                DatabaseColumn.INSTRUCTOR_ID: "INS101",
                DatabaseColumn.DEPARTMENT: "FOO",
                DatabaseColumn.COURSE_CODE: "BAR",
                DatabaseColumn.SECTION_NUMBER: 1,
                DatabaseColumn.CLASS_NAME: "BAZ",
                DatabaseColumn.CURRENT_ENROLLMENT: 0,
                DatabaseColumn.MAX_ENROLLMENT: 10,
                DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: True,
            },
            {
                DatabaseColumn.INSTRUCTOR_ID: "INS102",
                DatabaseColumn.DEPARTMENT: "QUX",
                DatabaseColumn.COURSE_CODE: "QUUX",
                DatabaseColumn.SECTION_NUMBER: 1,
                DatabaseColumn.CLASS_NAME: "CORGE",
                DatabaseColumn.CURRENT_ENROLLMENT: 0,
                DatabaseColumn.MAX_ENROLLMENT: 10,
                DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN:False,
            },
        ]
        self._class_repository.save_all(class_data)
        self.assertEqual(self._class_repository.count_by_attribute(), self._init_count+2)

    def test_find_by_attribute(self):
        self.assertEqual(self._class_repository.count_by_attribute({DatabaseColumn.MAX_ENROLLMENT: 10, DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: False}), 1)

    def test_exists_by_attribute(self):
        self.assertTrue(self._class_repository.exists_by_attribute({DatabaseColumn.INSTRUCTOR_ID: "INS101"}))
        self.assertFalse(self._class_repository.exists_by_attribute({DatabaseColumn.INSTRUCTOR_ID: "INS100"}))

    def test_delete_by_attribute(self):
        self._class_repository.delete_by_attribute({DatabaseColumn.ID: "c25ccf22-4539-4810-b78b-81049b546bf1"})
        self.assertEqual(self._class_repository.count_by_attribute(), self._init_count-1)

    def test_find_all_by_attribute(self):
        class_data = self._class_repository.find_all_by_attribute({DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: True})
        self.assertEqual(len(class_data), 2)

    def test_count_by_attribute(self):
        self.assertEqual(self._class_repository.count_by_attribute({DatabaseColumn.MAX_ENROLLMENT: 10, DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: False}), 1)
