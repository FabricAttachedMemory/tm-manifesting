#!/usr/bin/python3
from contextlib import contextmanager
import errno
import glob
import logging
import os
import shutil
import stat
import sys
import urllib.request

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
        allowed_path = '/' + '/'.join(allowed)
        if target.startswith(allowed_path):
        #if allowed == elems[:allowed_size]:
            isNotAllowed = False
            break

    assert isNotAllowed is False, 'Target is not under any of the allowed dirs: %s' % (_allowed_dirs)
    #assert elems[:2] == ['var', 'lib'], 'Target is not under /var/lib'


def copy_target_into(target, into, verbose=False):
    """
        Wrapper around shutil.copy* functions. Main intention is to catch a
    specific exception and raise RuntimeError with a meaningful message. Also
    provides debugging and verbose options.

    :param 'target': [str] path to an object that needs to be copied.
    :param 'into': [str] path to the destination object (dir path or filename)
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        _fs_sanity_check(into)
        if os.path.isdir(target):
            shutil.copytree(target, into)   # copy directory
        else:
            if os.path.isdir(into):
                into += '/' + os.path.basename(target)
            shutil.copyfile(target, into)   # copy single file
        logging.info(' - Copy completed: from %s into %s' % (target, into))
    except (AssertionError, RuntimeError, EnvironmentError) as err:
        raise RuntimeError('Couldn\'t copy "%s" into "%s": %s' % (
            target, into, str(err)))


def move_target(target, into, verbose=False):
    """
        Move target folder into new folder. NOTE: target will be removed!
    """
    logging.info(' -- Moving %s into %s' % (target, into))
    if target == into:
        return False
    copy_target_into(target, into, verbose=verbose)
    orig_content = glob.glob(target + '/*')
    copied_content = glob.glob(into + '/*')

    # verified number of files of copied files with original
    if len(orig_content) != len(copied_content):
        logging.error(
            ' - Failed to move() %s into %s! Copied content is not the same.')

        remove_target(into, verbose=verbose)
        return False

    # copied and original content seems to be the same. Thus, can remove target.
    remove_target(target, verbose=verbose)
    return True


def make_dir(path, exit_ok=True):
    """
        A simple wrapper around os.makedirs that skip existing folders.
    :param 'path': [str] Leave this routine with a (new) directory at path
    :return: None or raised error
    """
    try:
        os.makedirs(path, exist_ok=exit_ok)
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


def remove_target(target, verbose=False):
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
        logging.info(' - %s has been removed!' % target)
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


def write_to_file(target, content, is_append=False):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite
    :param 'content': [str] content to use in the new/overwritten file.
    """
    try:
        _fs_sanity_check(target)
        file_content = ''
        write_mode = 'a' if is_append else 'w'
        with open(target, write_mode) as file_obj:
            content_to_write = '%s\n' % (content)
            file_obj.write(content_to_write)
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


def from_url_or_local(target, destination):
    """
        Download a file into destination whether it is a local path or a url.

    @param target: str local path or url that needs to be saved into destination.
    @param destination: str path to where to save target file. Can path either
                        as dir/ or dir/file_name. When dir/ is used, a file
                        name same as of a target will be used.
    """
    if os.path.isdir(destination):
        #getting basename from url str works too
        destination = destination + '/' + os.path.basename(target)

    if os.path.exists(target):
        if not os.path.isfile(target):
            raise RuntimeError(' - E - %s is not a file!' % target)

        # Desired effect is a valid destination.  Is it done already?
        if os.path.realpath(target) == os.path.realpath(destination):
            return
        copy_target_into(target, destination)
    else:
        try:
            with urllib.request.urlopen(target) as url_file:

                with open(destination, 'wb') as out_file:
                    data = url_file.read() # a `bytes` object
                    out_file.write(data)
        except urllib.error.HTTPError as err:
            raise RuntimeError('Failed to download %s from url:\n - %s' %\
                                (target, err))
