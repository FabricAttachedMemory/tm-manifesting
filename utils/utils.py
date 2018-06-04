#!/usr/bin/python3 -tt
'''Every real project needs a utils module.'''

import collections
import errno
import glob
import logging
import os
import psutil
import requests as HTTP_REQUESTS
import shlex
import shutil
import signal
import time
import tarfile


from pdb import set_trace


###########################################################################
# The theoretical client ID is the full node coordinate but Bring Up has
# something else going on :-(.  However, when AA is finally real this will
# just retrieve the value that was originally taken from /etc/tmconfig in
# a giant circle of life and this routine can NOOP.  No blood no foul.
def setDhcpClientId(node):
    node.DhcpClientId = node.coordinate
    if not os.path.exists('/etc/default/bupxefix'):
        return
    URL = node.nodeMp.mfwApiUri + '/MgmtService/Mgmt/Hardware'
    try:
        resp = HTTP_REQUESTS.get(URL)
        assert resp.status_code == 200, \
            'Bad response code %d' % resp.status_code
        mpCoord = resp.json()['Coordinate']
        node.DhcpClientId = mpCoord.split('/SocBoard')[0]
    except Exception as e:
        pass


def _kill_pid_object(p):
    '''Utility routine for kill_pid and kill_chroot_daemon'''
    logging.debug('Killing PID %d (%s)' % (p.pid, p.cmdline()))
    try:
        os.kill(p.pid, signal.SIGTERM)
        time.sleep(0.5)
        if p.pid in psutil.pids():    # SIGTERM needs a boost
            os.kill(p.pid, signal.SIGKILL)
            time.sleep(0.5)
    except Exception as e:
        logging.warning('Killing PID %d FAILED: %s' % (p.pid,str(e)))
        pass

###########################################################################


def kill_pid(pid, procname='', daemon=True):
    '''Find a PID with optional qualifications and kill it.'''
    if pid not in psutil.pids():
        return False
    for p in psutil.process_iter():
        if p.pid != pid:
            continue
        if procname and p.name() != procname:
            continue
        if daemon and p.ppid() != 1:
            continue
        _kill_pid_object(p)
        return True
    return False

###########################################################################
# Some packages (nscd, nslcd) start their daemons after installation.
# If I'm in an ARM chroot, they live after the chroot exits.  Kill them.
# In a cascade situation, sometimes the /proc/<PID>/root link is changed
# to '/some/path (deleted)'.  This routine still works.


def kill_chroot_daemons(rootBase):
    """ Kill QEMU static programs with a root path that includes rootBase """
    assert not os.geteuid(), 'Only root can use kill_chroot_daemon'
    for p in psutil.process_iter():
        cmdline = p.cmdline()
        if (not cmdline or
            'qemu-aarch64-static' not in cmdline[0] or
            p.ppid() != 1):
                continue
        if not p.cwd().startswith(rootBase):
            continue
        _kill_pid_object(p)
