# Logging

This is the logging utility for every LoansBot application. Log messages are
sent directly to postgres. The package name is lblogging.

## Reasoning

A fairly helpful and regularly used mod-only section of the LoansBot website
is the ability to read the logs. Prior to the v2 update, logs were stored in
plaintext using the default apache logger format. This meant that either the
server or the client had to do a lot of processing to serve requests from only
a certain timeperiod, and rollover period were forced to be harsh (i.e., last
48 hours suddenly jumps to last 24 hours when rolling over).

The postgres database should be capable of managing these log messages now that
it has gone significant infrastructure upgrades. This provides a number of
advantages

- Now that we're not working in a monolith, it's extremely helpful if we can
  see logs that are a combination of many different microservices.
- Without a centralized log store, the differences between system time will
  make it difficult to determine order of events and performance.
- A relational storage gives a lot of flexibility for the website in display,
  especially for specific time ranges or by severity.

## Usage

```py
from lblogging import Logger, Level
import psycopg2

# Replace these strings with the real values
# You typically want a connection dedicated to just the logger to avoid
# logging interfering with transactions
conn = psycopg2.connect(
    host='database host',
    port='database port',
    user='database user',
    password='password',
    dbname='database name'
)
conn.autocommit = True

# Any identifier for the logger can be used, but if using a different
# logger for each file as is relatively common, the filename is fine. usually
# application + filename + log message makes it pretty easy to find the logging
# statement for debugging
lgr = Logger('my_appname', 'my_filename.py', conn)
lgr.prepare()
lgr.print(Level.TRACE, 'This is a {} message with formatting', 'trace')
lgr.print(Level.DEBUG, 'This is a debug message')
lgr.print(Level.INFO, 'This is an info message')
lgr.print(Level.WARN, 'this is a warning')
lgr.print(Level.ERROR, 'this is an error-level message (aka fatal)')

try:
    i = 1 / 0
except ZeroDivisionError:
    # note we don't need to pass the exception
    lgr.exception(Level.WARN)


# Combine multiple into one transaction
lgr.connection.autocommit = False
lgr.print(Level.TRACE, 'This will not be sent immediately')
lgr.print(Level.INFO, 'This wont be sent yet')
lgr.connection.commit()

# Prevent any log messages lower than INFO from being sent in the future
lgr.level = Level.INFO
lgr.print(Level.TRACE, 'This is not {} or formatted', 'sent')
lgr.print(Level.INFO, 'This is sent')
lgr.connection.commit()

# Create a copy of a logger with the same connection and app but a different
# identifier:
new_lgr = lgr.with_iden('other_filename.py')
```
