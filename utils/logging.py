#!/usr/bin/python3
"""
    A helper script to wrap logging module that will simplify its usage
around the blueprint scirpts and other similar behaviour.
"""
import logging
import sys
import os

from flask.wrappers import Response as flaskResponse  # type checking
from pdb import set_trace


class tmmsLogger(object):   # FIXME: how about subclassing getLogger?
    """
        Wrapper around logging module to allow a simpler Log handling.
    """

    _rootlogger = None

    @classmethod
    def reconfigure_rootlogger(cls,
            rootlogger=None, use_stderr=True, use_file='',
        level=logging.INFO):

        if cls._rootlogger is not None:     # locking built into logging
            return

        assert bool(use_stderr) ^ bool(use_file), \
            'Exactly one of use_stderr or use_file must be set'
        if rootlogger is None:
            rootlogger = logging.root
            assert rootlogger is not None, 'No root logger configured yet'

        if use_stderr:                  # That was easy
            logging.basicConfig(        # Idempotent, first call wins
                stream=sys.stderr,
                format='%(asctime)s %(levelname)-5s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=level)
        else:
            raise NotImplementedError('Rotating file is not implemented yet')

        cls._rootlogger = rootlogger

    def __init__(self, loggername, level=logging.INFO):
        # Create a logger with no handlers.   Because there is no "dot"
        # hierarchy in the namespace, its parent is the (default) root logger
        # and its handler, currently set by logging.basicConfig.  Since this
        # new logger has no handlers, it may fall up to its parent based
        # on its propagate flag (default True).
        # Insure there is a root logger, default to stderr and INFO.
        self.reconfigure_rootlogger()
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
