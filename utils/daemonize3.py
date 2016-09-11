#!/usr/bin/python3 -tt
'''
Daemonize a process in python3.  Acts like daemon(3), taken from somewhere
on Stack Overflow.  There wasn't a package for python3 in Jessie in 2016.
'''
import atexit
import errno
import time
import os
import signal
import sys
from pdb import set_trace


class Daemon(object):
    """
     Daemonization controller
     Script based of this: https://gist.github.com/marazmiki/3618191

     This class keeps track of the PID of the daemon by creating a pid_file
     in the specified location. It allows to check the status, start and stop
     the daemon.  If the process was interupted and the PID file was not
     cleaned up - the next daemon start will check if PID is alive and 
     override it if it is dead.
    """

    def __init__(self, pid_file=None, chdir=None, no_share_stream=False):
        self.chdir = chdir
        self.no_share_stream = no_share_stream

        if pid_file is None:
            self.pid_file = '/var/lib/tmms/server.pid'

    def start(self):
        """
            Start damonization. First, check if there is a PID file for the
        server already and if it is still running. Do not allow overrides,
        unless PID is already dead. Clean up and run the daemon.
        """
        pid = self.isAlive
        if pid:
            raise RuntimeError('Process already running... PID: %s' % pid)
        child1pid = self.spawn_a_child()
        if child1pid:   # I am the original parent
            os.wait(child1pid);
            return

        # I am child1
        self.detach()
        child1pid = self.spawn_a_child()
        self.delete_pidfile()
        self.create_pidfile(os.getpid())

        if not self.no_share_stream:
            dev_null = open('/dev/null', 'w')
            os.dup2(dev_null.fileno(), sys.stdin.fileno())  # yes, error on read
            os.dup2(dev_null.fileno(), sys.stdout.fileno())
            os.dup2(dev_null.fileno(), sys.stderr.fileno())

    def stop(self):
        """
            Stop the daemon. Throw a RuntimeError if PID doesn't exist or system
        failed to kill an existed process.
        """
        pid = self.get_pid()
        if not pid:
            # FIXME: LOGGER here
            raise RuntimeError('Daemon is not running. Nothing to stop.')
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
        """ Get status string of the daemon. """
        pid = self.isAlive
        if not pid:
            return 'Not Running'
        else:
            return 'Running with PID = %s' % pid


    def detach(self):
        """ Detach from current directory and from the parent process."""
        if self.chdir:
            if isinstance(self.chdir, str):
                os.chdir(self.chdir)
            else:
                os.chdir('/')
            # FIXME: LOGGER here
        os.setsid()
        os.umask(0o022)

    def spawn_a_child(self):
        """ Spawn the child process """
        forked = None
        try:
            return os.fork()
        except OSError as err:
            raise RuntimeError('PID %d fork() failed: %s' % (
                os.getpid(), str(err)))

    def create_pidfile(self, pid):
        """ Create pid file """
        atexit.register(self.delete_pidfile)    # FIXME: review this danger
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

    @property
    def isAlive(self):
        """
            Check if the PID saved in the pid_file is currently running.

        :return: None - process is not running or doesn't exists. PID - otherwise.
        """
        pid = self.get_pid()
        if pid is None:
            return None
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return None
            raise RuntimeError ('Faild to check PID=%s status: ' % (pid, str(err)))
        else:
            return pid

