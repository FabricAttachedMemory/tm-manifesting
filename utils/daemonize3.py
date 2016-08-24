#!/usr/bin/python3 -tt
'''
Daemonize a process in python3.  Acts like daemon(3), taken from somewhere
on Stack Overflow.  There wasn't a package for python3 in Jessie in 2016.
'''
import atexit
import time
import os
import signal
import sys

class Daemon(object):
    """ Daemonization controller """
    """ Script based of this: https://gist.github.com/marazmiki/3618191 """

    def __init__(self, pid_file=None, chdir=True, noclose=False):
        self.chdir = chdir
        self.noclose = noclose

        if pid_file is None:
            self.pid_file = '/var/lib/tmms/server.pid'
        else:
            self.pid_file = pid_file


    def start(self):
        """ Start damonization """
        pid = self.get_pid()
        if pid:
            raise RuntimeError('Process already running... PID: %s' % pid)
        pid = self.spawn_a_child()
        self.detach()
        pid = self.spawn_a_child()
        self.create_pidfile(os.getpid())

        if not self.noclose:
            dev_null = open('/dev/null', 'w')
            os.dup2(dev_null.fileno(), sys.stdin.fileno())  # yes, error on read
            os.dup2(dev_null.fileno(), sys.stdout.fileno())
            os.dup2(dev_null.fileno(), sys.stderr.fileno())


    def stop(self):
        """ Stop the daemon """
        pid = self.get_pid()
        if not pid:
            # FIXME: LOGGER here
            raise RuntimeError('No PID found for this daemon!')
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if 'No such process' in str(err):
                self.delete_pidfile()
            else:
                raise RuntimeError('Failed to stop process %s!' % pid)


    def status(self):
        """ Get status of the daemon: running, failed, stopped """
        pid = self.get_pid()
        if not pid:
            return 'Not Running'
        else:
            return 'Running with PID = %s' % pid


    def detach(self):
        """ Detach from current directory and from the parent process."""
        if self.chdir:
            os.chdir('/')
            # FIXME: LOGGER here
        os.setsid()
        os.umask(0o022)


    def spawn_a_child(self):
        """ Spawn the child process """
        forked = None
        try:
            forked = os.fork()
            if forked != 0:
                os._exit(0)
            # FIXME: LOGGER here
        except OSError as err:
            raise RuntimeError('Fork from PID %s faild: "%s"' % (os.getpid(), err))
        return forked


    def create_pidfile(self, pid):
        """ Create pid file """
        atexit.register(self.delete_pidfile)
        with open(self.pid_file, 'w') as file_obj:
            file_obj.write(str(pid).strip())


    def delete_pidfile(self):
        """ Delete pid file """
        if not os.path.exists(self.pid_file):
            return
        try:
            os.remove(self.pid_file)
        except OSError:
            raise RuntimeError('Failed to delete pid_file at %s!' % self.pid_file)


    def get_pid(self):
        """ Get PID of the process by looking at pid_file contents. """
        pid = None
        if not os.path.exists(self.pid_file):
            return None
        try:
            with open(self.pid_file, 'r') as file_obj:
                pid = int(file_obj.read().strip())
        except TypeError as err:
            pid = None
        return pid
