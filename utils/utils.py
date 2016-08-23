#!/usr/bin/python3 -tt
'''Every real project needs a utils module.'''
from contextlib import contextmanager
import errno
import os
import shlex
import shutil
import sys
import tarfile

from subprocess import call, Popen, PIPE
from tmms.utils.file_utils import remove_target


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
    try:
        cmd = shlex.split(cmdstr)
        assert not (use_call and return_process_obj), \
            'Flags are mutually exclusive'
        if return_process_obj:
            return Popen(cmd)
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


def ratify(path):
    """
        Validate path (or list of path) exist on the system. Save each
    non-existing path and return it in a list in the end.

    :param 'path': [list or str] list of pathes to validate or a signle path.
    :return: [list] of non-existing pathes.
    """
    if not path:
        return []

    if not isinstance(path, list):
        path = [path]

    missing_path_list = []
    for to_validate in path:
        if not os.path.exists(to_validate):
            missing_path_list.append(to_validate)

    return missing_path_list


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
        destination = destination + '/untar'
        remove_target(destination)  # succeeds even if missing
        with tarfile.open(source) as tar_obj:
            tar_obj.extractall(path=destination)
        return destination
    except (AssertionError, tarfile.ReadError, tarfile.ExtractError) as err:
        raise RuntimeError('Error occured while untaring "%s": %s' % (source, str(err)))


@contextmanager
def workdir(path):
    """
        Change script's work directory to perform a set of operation.
    Set original directory back when done.
    """
    try:
        orig_dir = os.getcwd()
        os.chdir(path)
        yield
    except OSError as e:
        raise RuntimeError('os.chdir(%s) failed: %s' % (path, str(e)))
    finally:
        os.chdir(orig_dir)
