#!/usr/bin/python3 -tt
"""
    Set of tests for for tmcmd/tm_task.py part of API.
"""

import unittest
import tmcmd


class TaskTest(unittest.TestCase):

    URL = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
    tm_cmd = None
    task_name = 'golden.l4tm.amd64.tar'


    @classmethod
    def setUpClass(cls):
        cls.tm_cmd = tmcmd.tmsysimg


    def test_golden_exists(self):
        """ Test if showtask can return non-error data for the task. """
        output = self.tm_cmd.listsysimgs()
        status = 'golden.l4tm.amd64.tar' in output
        self.assertTrue(status,
            msg='"golden.l4tm.amd64.tar" system-image should be in the list')


if __name__ == '__main__':
    unittest.main()
