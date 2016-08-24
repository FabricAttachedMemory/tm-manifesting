#!/usr/bin/python3 -tt
'''
Daemonize a process in python3.  Acts like daemon(3), taken from somewhere
on Stack Overflow.  There wasn't a package for python3 in Jessie in 2016.
'''

import os
import sys

class Daemon(object):
    """ Daemonization controller """

    def __init__(self, pid_file=None, nochdir=False, noclose=False):
        self.nochdir = nochdir
        self.noclose = noclose

        if pid_file is None:
            self.pid_file = '/var/lib/tmms/server.pid'
        else:
            self.pid_file = pid_file


    def start(self):
        """ Start daemonization"""
        raise NotImplementedError('Not done yet!')


    def detach(self):
        """ Detach from current directory and from the parent process."""
        os.chdir('/')
        os.setsid()
        os.umask(0)


    def spawn_a_child(self):
        """ Spawn the child process """
        try:
            forked = os.fork()
            if forked != 0:
                os._exit(0)
        except OSError as err:
            raise RuntimeError('Fork faild: "%s"' % err)

    def create_pidfile(self):
        """ Create pid file """


    def delete_pidfile(self):
        """ Delete pid file """
        try:
            os.remove(self.pid_file)
        except OSError:
            raise RuntimeError('Failed to delete pid_file at %s!' % self.pid_file)


    @property
    def pid(self):
        """ Get PID of the process by looking at pid_file contents. """
        pid = None
        try:
            with open(self.pid_file, 'r') as file_obj:
                pid = int(file_obj.read().strip())
        except TypeError as err:
            pid = None
        return pid




def daemonize(nochdir=False, noclose=False):
    '''Daemonize a process ala daemon(3)'''

    # first fork
    try:
        pid = os.fork()
        if pid > 0:
            raise SystemExit(0)     # exit first parent
    except OSError as e:
        raise SystemExit("fork #1 failed: %d (%s)" % (e.errno, e.strerror))

    # decouple from parent environment.  setsid is the real voodoo.
    if not nochdir:
        os.chdir("/")
    os.setsid()
    os.umask(0o022)

    # second fork
    try:
        pid = os.fork()
        if pid > 0:
            raise SystemExit(0)     # exit second parent
    except OSError as e:
        raise SystemExit("fork #2 failed: %d (%s)" % (e.errno, e.strerror))

    if not noclose:
        dev_null = open('/dev/null', 'w')
        os.dup2(dev_null.fileno(), sys.stdin.fileno())  # yes, error on read
        os.dup2(dev_null.fileno(), sys.stdout.fileno())
        os.dup2(dev_null.fileno(), sys.stderr.fileno())
