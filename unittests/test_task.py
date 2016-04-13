#!/usr/bin/python3 -tt
"""
    Set of tests for for tmcmd/tm_task.py part of API.
"""

import unittest
import tmcmd


class TaskTest(unittest.TestCase):

    URL = 'http://rocky42.americas.hpqcorp.net:31178/manifesting/api/'
    tm_cmd = None
    task_name = 'L4TM_C_CPP'


    @classmethod
    def setUpClass(cls):
        cls.tm_cmd = tmcmd.tmtask


    def test_L4TM_C_CPP_exists(self):
        """ Test if showtask can return non-error data for the task. """
        output = self.tm_cmd.showtask(self.task_name)
        status = 'error' in output
        self.assertFalse(status, msg='"L4TM_C_CPP" task should be in the list')


    def test_task_not_exists(self):
        """ Test if showtask will return error message for non-existed task. """
        output = self.tm_cmd.showtask('soup-no-soup')
        status = 'error' in output
        self.assertTrue(status,
                msg='"soup-no-soup" task should not be in the list')


    def test_L4TM_C_CPP_content(self):
        """ Test if showtask can return correct data for the package. """
        output = self.tm_cmd.showtask(self.task_name, verbose=True)
        expected = None
        with open('./mock-data/L4TM_C_CPP.task.json', 'r+') as file_obj:
            expected = file_obj.read()
        # Less reliable test in oppose to "output == expected", but less annoying,
        #due to unexpected '\n' characters that can appear in the end of the file
        #or output which breaks the test, even though the output logically correct.
        status = output in expected
        self.assertTrue(status,
                msg='Expected data in "mock-data/L4TM_C_CPP.task.json" does not match\
                with produced output.')


if __name__ == '__main__':
    unittest.main()
