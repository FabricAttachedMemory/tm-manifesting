#!/usr/bin/python3
"""
    A helper script to wrap logging module that will simplify its usage around the
blueprint scirpts and other similar behaviour.
"""
import os
import logging
import flask

from pdb import set_trace

class Logger(object):
    """
        Wrapper around logging module to allow a simplier Log handling.
    """

    def __init__(self, filename, app_name, formatter=None, level=None, disabled=False):
        self.filename = filename
        self.name = app_name
        self.disabled = disabled

        self.formatter = formatter
        if not self.formatter:
            self.formatter = '%(asctime)s :: %(levelname)s <%(name)s>:: %(message)s'

        self.level = level
        if not self.level:
            self.level = logging.INFO

        logging.basicConfig(filename=filename, format=self.formatter,
                            level=self.level)

        self.logger = logging.getLogger(app_name)
        self.logging = logging


    def level_func(self, lvl):
        """
            Convert logging level types passed as a string into an actual
        logging function.
        If invalid lvl string was passed - return logging.info
        """
        if not isinstance(lvl, str):
            return logging.info

        if lvl is None:
            lvl = 'info'

        if lvl.lower() == 'debug':
            if self.logger.level == logging.DEBUG:  # can't logging.debug unless
                return logging.debug                # logging.level is set to Debug

        types = {
                'info' : logging.info,
                'error' : logging.error,
                'warning' : logging.warning
                }
        return types.get(lvl.lower(), logging.info)


    def shutdown(self):
        logging.shutdown()


    def __call__(self, msg, level=None):
        if isinstance(msg, flask.wrappers.Response):
            if msg.status_code >= 400:
                logging.error(msg.response[0].decode())
            else:
                logging.info(msg.response[0].decode())
            return

        level = self.level_func(level)

        if isinstance(msg, str):
            level(msg)


    # Behave like a regular logging.info, logging.error and etc
    def info(self, msg):
        self.__call__(msg, 'info')
    def error(self, msg):
        self.__call__(msg, 'error')
    def warnig(self, msg):
        self.__call__(msg, 'warning')
    def debug(self, msg):
        self.__call__(msg, 'debug')
