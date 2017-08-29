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
    _format = '%(asctime)s %(levelname)-5s %(name)s: %(message)s'
    _datefmt = '%Y-%m-%d %H:%M:%S'

    @classmethod
    def _setup_filehandler(cls, use_file, backupCount=0):
        '''Level defaults to NOTSET ie everything is logged; append mode.'''
        # A single node build generates less than 2K of log data.
        h = logging.handlers.RotatingFileHandler(use_file,
            maxBytes=50*1024, backupCount=backupCount)
        h.setFormatter(logging.Formatter(cls._format, datefmt=cls._datefmt))
        return h

    @staticmethod
    def _remove_handlers(logger):
        logger.propagate = False        # prevent upper-level walk...
        while logger.hasHandlers():     # ...by this (RTFM)
            h = logger.handlers[-1]
            if hasattr(h, 'close'):     # file handler
                h.close()
            logger.removeHandler(h)

    @classmethod
    def reconfigure_rootlogger(cls,
            use_stderr=False, use_file='', verbose=False):

        cls._configured = True
        level = logging.DEBUG if verbose else logging.INFO

        # Clear out current handlers to allow re-use of basicConfig.
        rootlogger = logging.root       # old school: logging.getLogger('')
        cls._remove_handlers(rootlogger)

        if use_stderr:                  # does logging.RootLogger.addHandler()
            logging.basicConfig(        # only the first call matters
                stream=sys.stderr,
                format=cls._format,
                datefmt=cls._datefmt,
                level=level)

        if use_file:
            h = cls._setup_filehandler(use_file, backupCount=3)
            rootlogger.addHandler(h)
            rootlogger.setLevel(level)

    def __init__(self, loggername, use_file='', verbose=False):
        # Create a logger with no handlers.   Because there is no "dot"
        # hierarchy in the namespace, its parent is the (default) root logger
        # and its handler, currently set by reconfigure_rootlogger.  Since this
        # new logger has no handlers, it may fall up to its parent based
        # on its propagate flag (default True).
        # Insure there is a root logger, default to stderr and INFO.
        if not self._configured:     # locking built into logging
            self.reconfigure_rootlogger(use_stderr=True)
        self._logger = logging.getLogger(loggername)
        if use_file:    # could be separate from root handler's file
            h = self._setup_filehandler(use_file)
            self._logger.addHandler(h)
        level = logging.DEBUG if verbose else logging.INFO
        self._logger.setLevel(level)

    def _level_func(self, lvl):
        """
            Convert logging level types passed as a string into an actual
        logging function.
        If invalid lvl string was passed - return logging.INFO
        """
        if lvl is None or not isinstance(lvl, str):
            return self._logger.info
        return getattr(self._logger, lvl.lower(), self._logger.info)


    @property
    def propagate(self):
        if self._logger is None:
            raise RuntimeError('This logger has been shut down!')
        return self._logger.propagate


    @propagate.setter
    def propagate(self, value):
        if self._logger is None:
            raise RuntimeError('This logger has been shut down!')
        self._logger.propagate = value


    def shutdown(self):
        if self._logger is None:
            raise RuntimeError('This logger has been shut down!')
        self._remove_handlers(self._logger)
        self._logger = None


    def __call__(self, msg, level=None):
        if self._logger is None:
            raise RuntimeError('This logger has been shut down!')
        if isinstance(msg, flaskResponse):
            if msg.status_code >= 400:
                logger = self._logger.error
            else:
                logger = self._logger.info

            try:
                msg = msg.response[0].decode()
            except AttributeError:
                msg = msg.response[0]

        else:
            logger = self._level_func(level)
            msg = str(msg)
        logger(msg)


    # Behave like a regular logging.info, logging.error and etc
    _okattr = frozenset(('debug', 'info', 'warning', 'error', 'critical'))
    def __getattr__(self, attr):
        if self._logger is None:
            raise RuntimeError('This logger has been shut down!')
        if attr in self._okattr:
            return getattr(self._logger, attr)
        raise AttributeError(attr)
