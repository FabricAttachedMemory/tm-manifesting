#!/usr/bin/python3
"""
    A helper script to wrap logging module that will simplify its usage
around the blueprint scirpts and other similar behaviour.
"""
import logging
import logging.handlers
import sys
import os

from flask.wrappers import Response as flaskResponse  # type checking
from pdb import set_trace


class tmmsLogger(object):   # FIXME: how about subclassing getLogger?
    """
        Wrapper around logging module to allow a simpler Log handling.
    """

    _configured = False

    @classmethod
    def reconfigure_rootlogger(cls,
            use_stderr=False, use_file='', verbose=False):

        if cls._configured:     # locking built into logging
            return

        assert bool(use_stderr) ^ bool(use_file), \
            'Exactly one of use_stderr or use_file must be set'
        cls._configured = True
        level = logging.DEBUG if verbose else logging.INFO
        format='%(asctime)s %(levelname)-5s %(name)s: %(message)s'
        datefmt='%Y-%m-%d %H:%M:%S'

        if use_stderr:                  # does logging.RootLogger.addHandler()
            logging.basicConfig(        # only the first call matters
                stream=sys.stderr,
                format=format,
                datefmt=datefmt,
                level=level)
            return

        rootlogger = logging.root       # old school: logging.getLogger('')
        while rootlogger.hasHandlers():
            rootlogger.removeHandler(rootlogger.handlers[-1])
        h = logging.handlers.RotatingFileHandler(use_file,
            maxBytes=1024, backupCount=3)
        h.setFormatter(logging.Formatter(format, datefmt=datefmt))
        rootlogger.addHandler(h)
        rootlogger.setLevel(level)

    def __init__(self, loggername, level=logging.INFO):
        # Create a logger with no handlers.   Because there is no "dot"
        # hierarchy in the namespace, its parent is the (default) root logger
        # and its handler, currently set by logging.basicConfig.  Since this
        # new logger has no handlers, it may fall up to its parent based
        # on its propagate flag (default True).
        # Insure there is a root logger, default to stderr and INFO.
        self.reconfigure_rootlogger(use_stderr=True)
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(level)

    def level_func(self, lvl):
        """
            Convert logging level types passed as a string into an actual
        logging function.
        If invalid lvl string was passed - return logging.INFO
        """
        if lvl is None or not isinstance(lvl, str):
            return self.logger.info
        lvl = lvl.lower()

        types = {
                'critical' : self.logger.critical,
                'error' : self.logger.error,
                'warning' : self.logger.warning,
                'info' : self.logger.info,
                'debug' : self.logger.debug,
                }
        return types.get(lvl, self.logger.info)


    def shutdown(self):
        logging.shutdown()


    def __call__(self, msg, level=None):
        if isinstance(msg, flaskResponse):
            if msg.status_code >= 400:
                level = self.logger.error
            else:
                level = self.logger.info
            msg = msg.response[0].decode()
        else:
            level = self.level_func(level)
            msg = str(msg)

        level(msg)


    # Behave like a regular logging.info, logging.error and etc
    def critical(self, msg):
        self.__call__(msg, 'critical')
    def error(self, msg):
        self.__call__(msg, 'error')
    def warning(self, msg):
        self.__call__(msg, 'warning')
    def info(self, msg):
        self.__call__(msg, 'info')
    def debug(self, msg):
        self.__call__(msg, 'debug')
