from unittest import TestCase
from repository import ClassRepository
from sqlite3 import connect, Row
from util import DatabaseColumn, get_dummy_class, get_dummy_classes
import logging


class TestClassRepository(TestCase):

    @classmethod
    def setUp(cls):
        logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG)
        conn = connect("database.db", check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = Row
        cls._conn = conn
        cls._class_repository = ClassRepository(conn, "class", logger)

    @classmethod
    def tearDown(cls):
        cls._conn.close()

    def test_save(self):
        self._class_repository.save(get_dummy_class())
        self.assertEqual(self._class_repository.count_by_attribute(), 4)

    def test_save_all(self):
        self._class_repository.save_all(get_dummy_classes())
        self.assertEqual(self._class_repository.count_by_attribute(), 6)

    def test_count_by_attribute(self):
        self.assertEqual(self._class_repository.count_by_attribute({DatabaseColumn.MAX_ENROLLMENT: 10, DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: False}), 1)

    def test_find_by_attribute(self):
        self.assertEqual(self._class_repository.count_by_attribute({DatabaseColumn.MAX_ENROLLMENT: 10, DatabaseColumn.AUTOMATIC_ENROLLMENT_FROZEN: False}), 1)
