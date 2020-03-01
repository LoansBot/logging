"""Contains helpful messages for querying the existing logs. This is often
helpful in integration test suites for printing out the logs. This can be
used as a main function if the PG* env vars are set.
"""
from .level import Level
import psycopg2


def print_all_logs(conn, cursor):
    """Print all logs stored in the given database in a reasonable format.

    :param conn: The psycopg2 connection to use
    :param cursor: The psycopg2 cursor to use
    """
    query = (
        'SELECT '
          'log_applications.name, '  # noqa: E131
          'log_identifiers.identifier, '
          'log_events.level, '
          'log_events.message, '
          'log_events.created_at '
        'FROM log_events '
        'INNER JOIN log_applications '
          'ON log_applications.id = log_events.application_id '  # noqa: E131
        'INNER JOIN log_identifiers '
          'ON log_identifiers.id = log_events.identifier_id '  # noqa: E131
        'ORDER BY log_events.created_at DESC'
    )
    cursor.execute(query)
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        appname, iden, level_int, message, cat = row
        level = Level(level_int)
        print(f'  {cat} {level.name} [{appname} - {iden}] {message}')


def main():
    """Connect to the database using the default envvars then print all logs"""
    conn = psycopg2.connect('')
    cursor = conn.cursor()
    print_all_logs(conn, cursor)
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
