"""Describes a logger which connects to a postgres database. Assumes that the
postgres database already has the following tables

log_applications
- id: int primary key
- name: varchar unique

log_identifiers
- id: int primary key
- identifier: varchar unique

log_events
- id - int primary key
- level: int enum (0 = trace, 1 = debug, 2 = info, 3 = warn, 4 = error)
- application_id: int foreign key to log_applications(id)
- identifier_id: int foreign key to log_identifiers(id)
- message: text
- created_at: timestamp

We sacrifice some possibly useful features like multi-part messages and message
metadata for improved performance, especially at sorting time. It is not safe
to reuse the same postgres connection across threads/processes, but it is safe
to use multiple loggers with different connections across threads/processes.
"""
from .level import Level
from psycopg2.errors import UniqueViolation
import traceback


class Logger:
    """This instance provides a more conventional logging interface for sending
    log events to postgres.

    :param appname: The name of the application this logger is running within
    :type appname: str
    :param identifier: The identifier within the application for this logger,
        which is typically the filename
    :type identifier: str
    :param connection: The postgresql connection to use for sending log events
    :param level: The minimum log level which is sent to the postgres database.

    :param cursor: The cursor we use, initialized during prepare()
    :param app_id: The primary key within the postgres database for our
        application identifier. Initialized during prepare()
    :type app_id: int, optional
    :param iden_id: The primary key within the postgres database for our
        identifier. Initialized during prepare()
    :type iden_id: int, optional
    """
    def __init__(self, appname, identifier, connection, level=Level.TRACE):
        self.appname = appname
        self.identifier = identifier
        self.connection = connection
        self.level = level

        self.app_id = None
        self.iden_id = None
        self.cursor = None

    def prepare(self):
        """Prepare this logger for usage. This will fetch the app id and
        identifier and is required for fresh instances but not those that
        came from forfile
        """
        if self.cursor is not None:
            return

        self.cursor = self.connection.cursor()
        try:
            self.cursor.execute(
                'INSERT INTO log_applications (name) VALUES (%s) RETURNING id',
                (self.appname,)
            )
        except UniqueViolation:
            self.connection.rollback()
            self.cursor.execute(
                'SELECT id FROM log_applications WHERE name=%s',
                (self.appname,)
            )
        self.app_id = self.cursor.fetchone()[0]
        self.connection.commit()

        try:
            self.cursor.execute(
                'INSERT INTO log_identifiers ("identifier") VALUES (%s) RETURNING id',
                (self.identifier,)
            )
        except UniqueViolation:
            self.connection.rollback()
            self.cursor.execute(
                'SELECT id FROM log_identifiers WHERE "identifier"=%s',
                (self.identifier,)
            )
        self.iden_id = self.cursor.fetchone()[0]
        self.connection.commit()

    def print(self, level, message, *args):
        """Sends the given message to the database with the given loglevel. If
        the level is below that of this logger, it will be suppressed. If
        additional arguments are provided, the message is formatted with those
        arguments before being sent to the database. This does not explicitly
        commit, meaning the connection must be in autocommit mode or the callee
        must commit.

        :param level: The log-level for the message
        :param message: The message (or message format) to send
        :param args: Any additional arguments to format the message with
        """
        if level < self.level:
            return

        if args:
            message = message.format(*args)

        self._raw_insert(level, message)

    def exception(self, level, *args):
        """Sends the current exception to the database with the given loglevel. If
        arguments are provided, it is assumed the first argument is the message
        to pass along and the remaining arguments are used for formatting that
        message.

        :param level: The log-level for the message
        :param args: The message and format arguments if desired
        """
        if level < self.level:
            return

        message = []
        if args:
            message.append(args[0].format(*args[1:])).append('\n')

        message.append(traceback.format_exc())

        message = ''.join(message)
        self._raw_insert(level, message)

    def with_iden(self, identifier):
        """Provides a copy of this logger with the given identifier. This is
        faster than going through the constructor if prepare() has already been
        called.

        :param identifier: The identifier for the copy
        :return: a new Logger like this one but with the given identifier
        """
        cpy = Logger(self.appname, identifier, self.connection, self.level)
        cpy.cursor = self.cursor
        cpy.app_id = self.app_id
        cpy.iden_id = self.iden_id
        return cpy

    def _raw_insert(self, level, message):
        self.cursor.execute(
            'INSERT INTO log_events (level, application_id, identifier_id, message) VALUES (%s, %s, %s, %s)',
            (int(level), self.app_id, self.iden_id, message)
        )

    def close(self):
        """Explicitly close the resources opened by this logger. This will not
        shutdown the connection.
        """
        if self.cursor is None:
            return

        self.cursor.close()
        self.cursor = None
        self.app_id = None
        self.iden_id = None
