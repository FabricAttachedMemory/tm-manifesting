#!/usr/bin/python3 -tt
import os
import sys
import shutil

from pdb import set_trace

class Backuper(object):

    def __init__(self, target, destination):
        """
        """
        self.target = os.path.realpath(target)
        self.destination = os.path.realpath(destination)


    def backup(self):
        """
            Backup target into a destination location.
        """
        if os.path.isdir(self.destination):
            raise RuntimeError('Failed to backup [%s] into [%s]! Destination already exist.')
        if os.path.exists(self.destination):
            raise RuntimeError('Failed to backup [%s] into [%s]! Destination already exist.')

        self.copy(self.target, self.destination)


    def restore(self, replace=True):
        """
            Restore target from destination.
        """
        if os.path.isdir(self.destination) or os.path.exists(self.destination):
            if not replace:
                raise RuntimeError('Failed to restore into %s. '\
                      'Destination exists. Run with replace=False to force overwrite.')
            shutil.rmtree(self.destination)
        self.copy(self.destination, self.target)


    def copy(self, target, destination):
        """
            Copy target into destination.
        """
        if os.path.isdir(target):
            shutil.copytree(target, destination)
        else:
            shutil.copyfile(target, destination)
