#!/usr/bin/python3
"""
    A helper script to wrap logging module that will simplify its usage
around the blueprint scirpts and other similar behaviour.
"""
import os
import logging

from flask.wrappers import Response as flaskResponse  # type checking
from pdb import set_trace


class tmmsLogger(object):   # FIXME: how about subclassing getLogger?
    """
        Wrapper around logging module to allow a simpler Log handling.
    """

    def __init__(self, filename, loggername,
         formatter=None, level=logging.INFO):
        if not formatter:
            formatter = '%(asctime)s :: %(levelname)s <%(name)s>:: %(message)s'

        # Idempotent reconfiguration of root logger.  This chooses a simple
        # file handler FIXME remove/add a rotating file handler, process
        # VERBOSE and DEBUG from cmdline.
        logging.basicConfig(
            filename=filename,
            format=formatter,
            level=level)

        # Create a logger with no handlers.   Because there is no "dot"
        # hierarchy in the namespace, its parent is the (default) root logger
        # and its handler, currently set by logging.basicConfig.  Since this
        # new logger has no handlers, it will roll over to its parent based
        # on its propagate flag.
        self.logger = logging.getLogger(loggername) # propagate default: True

    def level_func(self, lvl):
        """
            Convert logging level types passed as a string into an actual
        logging function.
        If invalid lvl string was passed - return logging.info
        """
        if lvl is None or not isinstance(lvl, str):
            return self.logger.info
        lvl = lvl.lower()

        # Suppress logging.debug unless logging.level is set to Debug: WHY?
        if lvl == 'debug':
            if self.logger.level == logging.DEBUG:
                return self.logger.debug

        types = {
                'critical' : self.logger.critical,
                'error' : self.logger.error,
                'warning' : self.logger.warning,
                'info' : self.logger.info,
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
