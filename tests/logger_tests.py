"""Tests the logger"""
import unittest
import psycopg2
from pypika import Query, Table, analytics
from pypika.terms import Star
import sys


sys.path.append('../src')


from lblogging import Logger, Level


class LoggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection = psycopg2.connect('')
        cls.log_events = Table('log_events')
        cls.log_apps = Table('log_applications')
        cls.log_idens = Table('log_identifiers')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.connection = None

    def setUp(self):
        self.logger = Logger('lblogging', 'logger_tests.py', self.connection)
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

    def test_print_fails_without_prepare(self):
        with self.assertRaises(AttributeError):
            self.logger.print(Level.TRACE, 'some message')

    def test_creates_app_id(self):
        self.cursor.execute(
            Query.from_(self.log_apps).select(analytics.Count(Star())).get_sql()
        )
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 0)
        self.logger.prepare()
        self.cursor.execute(
            Query.from_(self.log_apps).select(analytics.Count(Star())).get_sql()
        )
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 1)
        self.cursor.execute(
            Query.from_(self.log_apps).select(self.log_apps.id, self.log_apps.name).get_sql()
        )
        id_, nm = self.cursor.fetchone()
        self.connection.commit()
        self.assertEqual(nm, self.logger.appname)
        self.assertEqual(id_, self.logger.app_id)

    def test_creates_iden_id(self):
        self.cursor.execute(
            Query.from_(self.log_idens).select(analytics.Count(Star())).get_sql()
        )
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 0)
        self.logger.prepare()
        self.cursor.execute(
            Query.from_(self.log_idens).select(analytics.Count(Star())).get_sql()
        )
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 1)
        self.cursor.execute(
            Query.from_(self.log_idens).select(self.log_idens.id, self.log_idens.identifier).get_sql()
        )
        id_, iden = self.cursor.fetchone()
        self.connection.commit()
        self.assertEqual(iden, self.logger.identifier)
        self.assertEqual(id_, self.logger.iden_id)

    def test_reuses_app_id(self):
        self.logger.prepare()
        new_lgr = Logger(self.logger.appname, 'iden2', self.connection)
        new_lgr.prepare()
        self.assertEqual(self.logger.app_id, new_lgr.app_id)

    def test_reuses_iden_id(self):
        self.logger.prepare()
        new_lgr = Logger(self.logger.appname, self.logger.identifier, self.connection)
        new_lgr.prepare()
        self.assertEqual(self.logger.iden_id, new_lgr.iden_id)

    def test_print_created_event(self):
        self.logger.prepare()

        self.cursor.execute(Query.from_(self.log_events).select(analytics.Count(Star())).get_sql())
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 0)
        self.logger.print(Level.TRACE, 'msg')
        self.connection.commit()
        self.cursor.execute(Query.from_(self.log_events).select(analytics.Count(Star())).get_sql())
        cnt = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(cnt, 1)
        self.cursor.execute(Query.from_(self.log_events).select('level', 'application_id', 'identifier_id', 'message').get_sql())
        lvl, appid, idenid, msg = self.cursor.fetchone()
        self.connection.commit()
        self.assertEqual(lvl, int(Level.TRACE))
        self.assertEqual(appid, self.logger.app_id)
        self.assertEqual(idenid, self.logger.iden_id)
        self.assertEqual(msg, 'msg')

    def test_print_formats_messages(self):
        self.logger.prepare()
        self.logger.print(Level.TRACE, 'my {} message', 'formatted')
        self.cursor.execute(Query.from_(self.log_events).select('message').limit(1).get_sql())
        msg = self.cursor.fetchone()[0]
        self.connection.commit()
        self.assertEqual(msg, 'my formatted message')

    def test_exception_event(self):
        self.logger.prepare()
        try:
            1/0
        except ZeroDivisionError:
            self.logger.exception(Level.WARN)

        self.cursor.execute(Query.from_(self.log_events).select('level', 'message').limit(1).get_sql())
        lvl, msg = self.cursor.fetchone()
        self.connection.commit()
        self.assertEqual(lvl, int(Level.WARN))
        self.assertIn('ZeroDivisionError', msg)

    def test_with_iden(self):
        self.logger.prepare()
        lgr = self.logger.with_iden('iden2')
        self.assertEqual(lgr.app_id, self.logger.app_id)
        self.assertEqual(lgr.iden_id, self.logger.iden_id)
        self.assertEqual(lgr.identifier, 'iden2')
        self.assertEqual(lgr.appname, self.logger.appname)


if __name__ == '__main__':
    unittest.main()
