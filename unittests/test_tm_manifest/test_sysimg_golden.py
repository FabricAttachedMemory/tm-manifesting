#!/usr/bin/python3 -tt
"""
    Set of tests for for tmcmd/tm_task.py part of API.
"""
import os
import shutil
import unittest
import tmcmd


class TaskTest(unittest.TestCase):

    URL = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
    tm_cmd = None
    task_name = 'golden.l4tm.amd64.tar'
    tmp_folder = '/tmp/UNITTEST_GOLDEN/'

    @classmethod
    def setUp(cls):
        cls.tm_cmd = tmcmd.tmsysimg
        if os.path.isdir(cls.tmp_folder):
            shutil.rmtree(cls.tmp_folder)
        os.makedirs(cls.tmp_folder)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            shutil.rmtree(cls.tmp_folder)


    def test_golden_exists(self):
        """ Test if showtask can return non-error data for the task. """
        output = self.tm_cmd.listall()
        status = 'golden.l4tm.amd64.tar' in output
        self.assertTrue(status,
            msg='"golden.l4tm.amd64.tar" system-image should be in the list')


    def test_golden_download(self):
        """ Test if can download golden image into destination (/tmp/UNITTEST_GOLDEN) """
        output_file = os.path.join(self.tmp_folder, 'golden.l4tm.amd64.tar')
        self.tm_cmd.download(['golden.l4tm.amd64.tar', output_file])

        downloaded = os.path.join(self.tmp_folder, 'golden.l4tm.amd64.tar')
        self.assertTrue(os.path.exists(downloaded),
                        '"golden.l4tm.amd64.tar" was not downloaded into "%s"!' % (self.tmp_folder))


if __name__ == '__main__':
    unittest.main()
