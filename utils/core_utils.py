#!/usr/bin/python3 -tt
'''
    Set of functions to be used across the whole project that do Not require any
install of non-standard python3 libraries. This script is also imported by
configs/setup_* scripts, therefore, to avoid any install conflicts, for any additional
functions to be added here, make sure they keep using only standard python3
libraries.
'''

import collections
import glob
import logging
import os
import shlex
import signal
import subprocess
import tarfile
import time
from pdb import set_trace

from . import file_utils


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
    with file_utils.workdir(start_path):   # walk relative to untar'ed FS folder.
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


def piper(cmdstr, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
          use_call=False, return_process_obj=False):
    """Pipe a command, maybe retrieve stdout/stderr, hides ugly output"""
    if stdout == '/dev/null':
        stdout = subprocess.DEVNULL
    if stderr == '/dev/null':
        stderr = subprocess.DEVNULL
    try:
        cmd = shlex.split(cmdstr)
        assert not (use_call and return_process_obj), \
            'Flags are mutually exclusive'
        if return_process_obj:
            return subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        if use_call:
            return subprocess.call(cmd), None, None

        if stdin is None:
            stdindata = None
        else:
            stdindata = stdin
            stdin = subprocess.PIPE

        p = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
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
        file_utils.remove_target(destination)  # succeeds even if missing
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


def deb_components(full_source):
    """
        Extract components(url, release, areas) of the sources.list entry into
    a nambedtuple object.
    When incorrectly formatted str is passed, all components are set to empty str.

    @param full_source: full url as it appears in sources.list (deb url release areas)
    """
    pieces = collections.namedtuple('DebianComponents', 'url release areas')
    #Need to set defaults for namedtuple params...
    pieces.url = ''
    pieces.release = ''
    pieces.areas = []

    #Silly check of the format of the source. If it doesn't even start with
    #'deb', there is no reason to try extracting compojnents.
    if not full_source.startswith('deb'):
        return pieces

    splitted = full_source.split(' ')
    # source url might have [trusted=yes] thingy in second position. Remove it.
    if not splitted[1].startswith('http'):
        splitted.pop(1)

    # size should be at least 4, cause "deb http//url release area1"
    if len(splitted) < 4:
        return pieces

    pieces.url = splitted[1]
    pieces.release = splitted[2]
    pieces.areas = splitted[3:]

    return pieces


def get_vars_from_file(path_to_vars=None, only=None):
    """Parse a file of shell (bash) environment variables."""
    if path_to_vars is None:
        path_to_vars = '/etc/environment'
    if only is None or not only:
        only = ()       # "None" means get them all

    try:
        with open(path_to_vars, 'r') as EE:
            env_lines = EE.read().split('\n')
        # Some ToRMS said "export xxx=yyy" or used quotes, bad robot!
        env_lines = [ line.strip().replace('export ', '')
            for line in env_lines ]
    except OSError as e:
        logging.error("Couldn't read %s: %s" % (path_to_vars, str(e)))
        return None

    result = {}
    for linenum, line in enumerate(env_lines):
        if not line or line.startswith('#'):
            continue
        try:
            var, val = line.split('=')
        except ValueError as e:     # Incorrect number of values to unpack
            logging.error("Ignoring %s line %d: %s" % (
                path_to_vars, linenum + 1, line))
            continue
        var = var.strip().split(' ')[-1]    # Ignore spaces, take final token
        if only and var not in only:
            continue
        val = val.strip('"\'')              # Remove quotes
        result[var] = val

    return result


def set_proxy_environment():
    '''If http[s]_proxy are not set, try to grab them from /etc/environment.
       Set them in os.environ for use by subprograms and subroutines.'''

    # What's in the environment?  It either came from systemctl under
    # /etc/systemd/system/tm-manifest-server.service.d/xxxx.conf or an
    # explicit set on the command line, or existing in the environment (like
    # from "sudo -E tm-manifest setup blah").  INVOCATION_ID is in os.environ
    # if this was started from systemctl.  Not sure if it matters...
    # no_proxy is observed by "requests" module.

    only = [ p for p in ('http_proxy', 'https_proxy', 'ftp_proxy', 'no_proxy')
            if p not in os.environ ]
    only = only or None
    os.environ.update(get_vars_from_file(only=only))


def create_loopback_files():
    """
    One loopback file is required for each node being bound to a manifest.
    One is also used during setup golden_image.  LXC doesn't prebuild them
    and I'm not sure why.  "loop" is statically compiled and that seems to
    lock the count at eight.
    """
    fname = '/dev/loop-control'
    file_utils.mknod(fname, 'char', 10, 237)
    file_utils.chgrp(fname, 'disk')
    for i in range(0, 8):
        fname = '/dev/loop%d' % i
        file_utils.mknod(fname, 'block', 7, i)
        file_utils.chgrp(fname, 'disk')


def parse_vmd(path):
    """
        Parse a VMD-like config (format: "variable_name=vlaue" per line) into a
    dictionary: <variable_name> : <value>.

    @param path: <str> path to a VMD-like config file to be parsed.
    @return: dictionary of config file's properties.
    """
    if not os.path.exists(path):
        return {}

    vmd_data = {}
    file_content = ''
    # Reading VMD(debootstrap) config file and getting Raw data.
    with open(path, 'r') as file_obj:
        file_content = file_obj.read()

    # Parsing VMD's "variable=value" format into dictionary
    for line in file_content.split('\n'):
        vmd_param = line.split('=')
        if len(vmd_param) != 2:
            continue

        vmd_data[vmd_param[0].strip()] = vmd_param[1].strip()

    return vmd_data
