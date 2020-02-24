"""Tests the queries"""
import unittest
import psycopg2
import sys


sys.path.append('../src')

from lblogging import Logger, Level
import lblogging.query


class LoggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection = psycopg2.connect('')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.connection = None

    def setUp(self):
        self.logger = Logger('lblogging', 'test_query.py', self.connection)
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.logger.close()
        self.logger = None
        self.connection.rollback()
        self.cursor.execute('TRUNCATE log_applications CASCADE')
        self.cursor.execute('TRUNCATE log_identifiers CASCADE')
        self.cursor.execute('TRUNCATE log_events CASCADE')
        self.connection.commit()
        self.cursor.close()
        self.cursor = None

    def test_print_all_logs_no_error_when_empty(self):
        lblogging.query.print_all_logs(self.connection, self.cursor)
        self.assertIsNone(None)

    def test_print_all_logs_no_errors_with_logs(self):
        self.logger.prepare()
        self.logger.print(Level.TRACE, 'Test trace message')
        lblogging.query.print_all_logs(self.connection, self.cursor)
