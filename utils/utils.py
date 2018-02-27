#!/usr/bin/python3 -tt
'''Every real project needs a utils module.'''

from contextlib import contextmanager
import errno
import logging
import os
import glob
import psutil
import requests as HTTP_REQUESTS
import shlex
import shutil
import signal
import time
import tarfile

from pdb import set_trace
from subprocess import call, Popen, PIPE, DEVNULL

from tmms.utils.file_utils import remove_target, workdir, mknod, chgrp


def basepath(fullpath, leading):
    '''Strip "leading" from "fullpath".  Certain restrictions may apply.'''
    for p in (fullpath, leading):
        assert p[0] == '/', '"%s" is not an absolute path' % p
    assert fullpath.startswith(leading), \
        '"%s" does not start with %s' % (fullpath, leading)
    tmp = fullpath[len(leading):]
    return tmp


def find(start_path, ignore_files=[], ignore_dirs=[]):
    """
        Emulating output of unix "find" command.  Must build a list of all
    the directories and filenames using os.walk relative to the start of its
    walking directory.
    Note: os.walk expands its data into three variables, where 'dirs' and
    'files' are not relative path, but  rather "basenames". Combining all
    together will result in a full path string. e.g:
      root + "/" dirs[0] + "/" + files[0] = /root/elemenOfDirs/elementOfFIles

    :param 'start_path': [str] path to start walk from.
    :param 'ignore_files': [list] filenames to ignore during the walk.
    :param 'ignore_dirs': [list] directories to ignore from walking through.
    :return: [list] all the walked directories and filenames  relative to the
            'start_path'.  This will save EACH directory relative path e,g:
            /path/to/top/ will be saved as /path/, /path/to/ and /path/to/top/
    """
    result = []
    with workdir(start_path):   # walk relative to untar'ed FS folder.
        for root, dirs, files in os.walk('.'):
            for dirname in dirs:    # each directory relative path to the root
                if dirname in ignore_dirs:
                    continue
                result.append(os.path.join(root, dirname))
            for filename in files:  # each filename relative path to the root
                if filename in ignore_files:
                    continue
                result.append(os.path.join(root, filename))
    return result

###########################################################################
# Sub-process caller that returns different things based on return_process_obj:
# False: return ret, stdout, stderr.  stdin is sent to child.  High level.
# True:  return process data.  stdin is NOT sent to child.  Low level.
# stdin is data to be written, versus a subprocess.CONSTANT.  If you just
# want to start the proc and wait, set use_call.


def piper(cmdstr, stdin=None, stdout=PIPE, stderr=PIPE,
          use_call=False, return_process_obj=False):
    """Pipe a command, maybe retrieve stdout/stderr, hides ugly output"""
    if stdout == '/dev/null':
        stdout = DEVNULL
    if stderr == '/dev/null':
        stderr = DEVNULL
    try:
        cmd = shlex.split(cmdstr)
        assert not (use_call and return_process_obj), \
            'Flags are mutually exclusive'
        if return_process_obj:
            return Popen(cmd, stdout=stdout, stderr=stderr)
        if use_call:
            return call(cmd), None, None

        if stdin is None:
            stdindata = None
        else:
            stdindata = stdin
            stdin = PIPE

        p = Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
        stdout, stderr = p.communicate(stdindata)        # implicit wait()
        ret = p.returncode
        if ret is None:
            ret = 0
        return ret, stdout, stderr
    except Exception as e:
        raise RuntimeError('"%s" failed: %s' % (cmdstr, str(e)))


def untar(destination, source):
    """
        Untar source file into destination folder. tar.tarfile.extractall
    will create all necessary (sub)directories.
    Note: When untaring into the existing folder to overwrite files,
    tarfile.extractall function will throw a FileExistsError
    if it can not overwrite broken symlinks of the tar'ed file.
    Nuke it from orbit, it's the only way to be sure.

    :param 'destination': [str] path to where to extract target into.
    :param 'source': [str] path to a .tar file to untar.
    :return: [str] path to untared content.  Raise RuntimeError on problems.
    """

    try:
        remove_target(destination)  # succeeds even if missing
        with tarfile.open(source) as tar_obj:
            tar_obj.extractall(path=destination)
        return destination
    except (AssertionError, tarfile.ReadError, tarfile.ExtractError) as err:
        raise RuntimeError('Error occured while untaring "%s": %s' % (source, str(err)))


def make_tar(destination, source):
    """ Make a "source" folder into "tar" destination. No compression involved."""
    with tarfile.open(destination, 'w') as tar:
        if os.path.isfile(source):
            tar.add(source, arcname=os.path.basename(source))
        else:
            # to avoid creating a folder of itself inside of the compressed file.
            for to_compress in glob.glob(source + '/*'):
                tar.add(to_compress, arcname=os.path.basename(to_compress))


def create_loopback_files():
    """
    One loopback file is required for each node being bound to a manifest.
    One is also used during setup golden_image.  LXC doesn't prebuild them
    and I'm not sure why.  "loop" is statically compiled and that seems to
    lock the count at eight.
    """
    fname = '/dev/loop-control'
    mknod(fname, 'char', 10, 237)
    chgrp(fname, 'disk')
    for i in range(0, 8):
        fname = '/dev/loop%d' % i
        mknod(fname, 'block', 7, i)
        chgrp(fname, 'disk')

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
    logging.info('Killing PID %d (%s)' % (p.pid, p.cmdline()))
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
    '''Kill QEMU static programs with a root path that includes rootBase'''
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
