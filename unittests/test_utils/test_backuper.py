#!/usr/bin/python3 -tt
"""
"""
from pdb import set_trace

import os
import sys
import unittest
from shutil import rmtree, copytree

from utils import Backuper
from pdb import set_trace


class UtilsBackuperTest(unittest.TestCase):

    target_file = './mock_data/backup.test'
    target_dir = './mock_data/test_backup/'
    destination = '/tmp/test_backuper/'

    @classmethod
    def setUp(cls):
        set_trace()
        if os.path.isdir(cls.destination):
            rmtree(cls.destination)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.destination):
            rmtree(cls.destination)


    def test_backup_file(self):
        """
        """
        set_trace()
        Backup = Backuper(self.target_file, self.destination)
        Backup.backup()
        self.assertTrue(os.path.exists(self.destination), 'File wasnt backup.')


    def test_restore_file(self):
        """
        """
        Backup = Backuper(self.target_file, self.destination)
        Backup.backup()
        self.assertTrue(os.path.exists(self.destination), 'File wasnt backup.')

        os.remove(self.target_file)

        Backup.restore()
        self.assertTrue(os.path.exists(self.target_file), 'File was not restored.')


if __name__ == '__main__':
    unittest.main()
