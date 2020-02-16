"""Contains the various log-level constants
"""
import enum


class Level(enum.IntEnum):
    TRACE = 0
    """Used for log messages which are typically used to follow control flow
    moreso than the action themself."""

    DEBUG = 1
    """Used for key variable values that might be useful to a developer
    debugging the results for resolving warnings/errors"""

    INFO = 2
    """Used to report outwardly visible events, such as when the loansbot
    detects a particular comment and has decided to act upon it"""

    WARN = 3
    """Used for things that are impairing the programs standard execution,
    or may indicate a configuration-error, but for which there is either a
    known recovery path or don't prevent the core functionality from occurring.
    """

    ERROR = 4
    """Used for unexpected and possibly unrecoverable situations. For stability
    the program may still attempt some extreme recovery method, such as
    restarting.
    """
