#!/usr/bin/python3
from contextlib import contextmanager
import errno
import os
import shutil
import stat
import sys
from pdb import set_trace

_allowed_dirs = [
            ['var', 'lib'],
            ['var', 'lib', 'tmp'],
            ['tmp']
                ]

def _fs_sanity_check(target):
    """
        Some file routines are HORRIBLY dangerous to run as root.
    Perform a few idiot checks.
    :param 'target': [str] path about to be copied/moved/overwritten/removed
    :return: 'None' on success. Raise 'AssertionError' on problems.
    """
    if os.geteuid():    # Not root?  Trust the FS
        return
    target = target.strip()
    assert target[0] == '/', 'Not an absolute path'
    elems = target.split('/')[1:]   # zeroth is empty string
    assert len(elems) > 2, 'Target is a primary directory'

    isNotAllowed = True
    for allowed in _allowed_dirs:
        allowed_size = len(allowed)
        if allowed == elems[:allowed_size]:
            isNotAllowed = False
            break

    assert isNotAllowed is False, 'Target is not under any of the allowed dirs: %s' % (_allowed_dirs)
    #assert elems[:2] == ['var', 'lib'], 'Target is not under /var/lib'


def copy_target_into(target, into):
    """
        Wrapper around shutil.copy* functions. Main intention is to catch a
    specific exception and raise RuntimeError with a meaningful message. Also
    provides debugging and verbose options.

    :param 'target': [str] path to an object that needs to be copied.
    :param 'into': [str] path to the destination object (dir path or filename)
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        _fs_sanity_check(target)
        if os.path.isdir(target):
            shutil.copytree(target, into)   # copy directory
        else:
            shutil.copyfile(target, into)   # copy single file
    except (AssertionError, RuntimeError, EnvironmentError) as err:
        raise RuntimeError('Couldn\'t copy "%s" into "%s": %s' % (
            target, into, str(err)))


def make_dir(path):
    """
        FIXME: all we need is ', exists_ok=True' and we can get rid of this.
        A simple wrapper around os.makedirs that skip existing folders.
    :param 'path': [str] Leave this routine with a (new) directory at path
    :return: None or raised error
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise RuntimeError('mkdir(%s) failed: %s' % (path, str(e)))


def make_symlink(source, target):
    '''
      Wrap os.symlink; succeed if target exists properly.  Used in setup.
    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :return: 'None' on success or raise 'RuntimeError'
    '''
    if not os.path.exists(os.path.realpath(source)):
        raise RuntimeError('Symlink failed! %s not found!' % source)
    try:
        os.symlink(source, target)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise RuntimeError('symlink(%s -> %s) failed: %s' % (
                source, target, str(e)))
        if not os.path.islink(target):
            raise RuntimeError('Existing "%s" is not a symlink' % target)
        if os.path.realpath(target) != source:
            raise RuntimeError(
                'Existing symlink "%s" does not point to %s' % (
                    target, source))


def remove_target(target):
    """
        Remove "target" file.

    :param 'target': [str] path to the file to remove.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        _fs_sanity_check(target)
        if os.path.isdir(target):
            shutil.rmtree(target)
        elif os.path.exists(target):
            os.remove(target)
    except (AssertionError, EnvironmentError) as e:
        raise RuntimeError('Couldn\'t remove "%s": %s' % (target, str(e)))


@contextmanager
def workdir(path):
    """
        Change script's work directory to perform a set of operation.
    Set original directory back when done.
    """
    assert path, 'Missing path'
    try:
        orig_dir = os.getcwd()
        os.chdir(path)
        yield
    except OSError as e:
        raise RuntimeError('os.chdir(%s) failed: %s' % (path, str(e)))
    finally:
        os.chdir(orig_dir)


def write_to_file(target, content):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite
    :param 'content': [str] content to use in the new/overwritten file.
    """
    try:
        _fs_sanity_check(target)
        with open(target, 'w+') as file_obj:
            file_content = '%s\n' % str(content)
            file_obj.write(file_content)
    except Exception as e:
        raise RuntimeError('Write "%s" failed: %s' % (target, str(e)))


def mknod(fname, devtype, major, minor, perms=0o660):
    '''Wrap mknod so it won't choke on existing file.'''

    mode = stat.S_IFBLK if devtype.lower()[0] == 'b' else stat.S_IFCHR
    device = os.makedev(major, minor)
    if os.path.exists(fname):   # see if it matches
        s = os.stat(fname)
        assert os.major(device) == os.major(s.st_rdev), 'Wrong devfile major'
        assert os.minor(device) == os.minor(s.st_rdev), 'Wrong devfile minor'
        mask = ~0o777           # Since I'm root, perms aren't critical
        assert mode == s.st_mode & mask, 'Wrong devfile type'
        return                  # My work here is done
    os.mknod(fname, mode=mode + perms, device=device)


def chgrp(fname, grpname):
    try:
        shutil.chown(fname, group=grpname)
    except OSError as e:
        raise RuntimeError('chown(%s) failed: %s' % (fname, str(e)))


