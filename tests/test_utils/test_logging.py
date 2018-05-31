#!/usr/bin/python3 -tt
"""
    Test utils/utils.py script.
"""
import flask
import logging
import os
import tempfile
import unittest
from shutil import rmtree

from tmms.utils import logging
from pdb import set_trace


class UtilsLoggerTest(unittest.TestCase):

    logfile = '/tmp/unittest_logging.log'
    app_name = 'test_log'
    logger = None

    @classmethod
    def setUp(cls):
        if os.path.exists(cls.logfile):     # From previous run
            os.remove(cls.logfile)
        logging.tmmsLogger.reconfigure_rootlogger(use_file=cls.logfile)
        cls.logger = logging.tmmsLogger(cls.app_name)

    '''
    @classmethod
    def tearDown(cls):
        """ Clean up test environment. """
        pass
    '''

    def test_logfile_created(self):
        """ Test if Logger class can create a log file """
        self.assertTrue(os.path.isfile(self.logfile))

    """
        Test if __call__ function of the Logger class can log messages based
    of the message type.
    """
    def test_call_default_info(self):
        msg = 'I am a default INFO of type string'
        self.logger(msg)
        self.assertTrue(self.isEntryInLog(msg, 'INFO'), 'default INFO Message was not logged.')

    def test_call_set_info(self):
        msg = 'I am a set INFO of type string'
        self.logger(msg, 'info')
        self.assertTrue(self.isEntryInLog(msg, 'INFO'), 'set INFO Message was not logged.')

    def test_call_set_debug_false(self):
        '''Logger opened at default level INFO so debug should NOT make it'''
        msg = 'I am a set DEBUG of type string'
        self.logger(msg, 'DEBUG')
        self.assertFalse(self.isEntryInLog(msg, 'DEBUG'), 'set DEBUG Message was not logged.')

    def test_call_set_debug_true(self):
        msg = 'I am a set DEBUG of type string'
        debug_logfile = '/tmp/unittest_logging.debug'
        if os.path.isfile(debug_logfile):
            os.remove(debug_logfile)
        self.logger = logging.tmmsLogger(
            'test_debug_log', use_file=debug_logfile, verbose=True)
        self.logger(msg, 'DEBUG')

        isEntryExist = self.isEntryInLog(msg, 'DEBUG')
        self.assertTrue(isEntryExist, 'set DEBUG Message was not logged.')

    def test_call_set_error(self):
        msg = 'I am a set ERROR of type string'
        self.logger(msg, 'ERROR')
        self.assertTrue(self.isEntryInLog(msg, 'ERROR'), 'set ERROR Message was not logged.')

    def test_call_set_warning(self):
        msg = 'I am a set WARNING of type string'
        self.logger(msg, 'WARNING')
        self.assertTrue(self.isEntryInLog(msg, 'WARNING'), 'set WARNING Message was not logged.')

    def test_call_response_200(self):
        status = 200
        level = 'INFO'
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

        status = 255
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

    def test_call_response_400(self):
        status = 400
        level = 'ERROR'
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

        status = 455
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

    def test_call_response_500(self):
        status = 500
        level = 'ERROR'
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

        status = 555
        resp = self.make_response('Response %s here.' % status, status)
        self.logger(resp)
        self.assertTrue(self.isEntryInLog(resp.get_data().decode(), level),
                        'Response type %s (%s) Message was not logged.' % (level, status))

    # Test inherited functions
    def test_inherit_info(self):
        msg = 'I am parent\'s INFO'
        level = 'INFO'
        self.logger.info(msg)
        isInLog = self.isEntryInLog(msg, level)
        self.assertTrue(isInLog, 'Parent\'s %s is not in log.' % level)

    def test_inherit_error(self):
        msg = 'I am parent\'s ERROR'
        level = 'ERROR'
        self.logger.error(msg)
        isInLog = self.isEntryInLog(msg, level)
        self.assertTrue(isInLog, 'Parent\'s %s is not in log.' % level)

    def test_inherit_warning(self):
        msg = 'I am parent\'s WARNING'
        level = 'WARNING'
        self.logger.info(msg)
        isInLog = self.isEntryInLog(msg, level)
        self.assertTrue(isInLog, 'Parent\'s %s is not in log.' % level)

    def test_shutdown(self):
        self.logger.shutdown()
        threwRuntimeError = False
        try:
            self.logger('This should throw a RuntimeError')
        except RuntimeError as e:
            threwRuntimeError = True
        self.assertTrue(threwRuntimeError, 'No RuntimeError after shutdown()')


    def isEntryInLog(self, entry, level=None, logfile=None):
        log_entries = None
        if logfile is None:
            logfile = self.logfile

        with open(logfile, 'r') as file_obj:
            log_entries = file_obj.read().strip().split('\n')
        for line in log_entries:
            if entry in line:
                if level is not None:
                    return level in line
                return True
        return False

    def make_response(self, msg, code):
        temp_app = flask.Flask('temp_make_response')
        resp = temp_app.make_response(msg)
        resp.status_code = code
        temp_ampp = None
        return resp


if __name__ == '__main__':
    unittest.main()
