#!/usr/bin/python3 -tt

# This script can be called directly (for use after git clone) or indirectly
# during dh_helper package builds.  Defer local imports until last moment
# as there are order dependencies.  Grab all possible arguments for all
# possible sub-scripts and do them (all).

import argparse
import os
import os.path
import sys

from pdb import set_trace


def link_into_python(args, git_repo_path):
    """
        Create a symlink to THIS manifesting source tree under the known
    Python hierarchy so that user could import manifesting libraries like
    "import tmms.foobar".  Keep it simple.  setup.py must be at the top.
    """
    py_ver = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
    tmptuple = (sys.prefix, py_ver)
    paths_to_lib = ('%s/local/lib/%s/dist-packages' % tmptuple,
                    '%s/lib/%s/dist-packages' % tmptuple)

    for path in paths_to_lib:
        if path not in sys.path:
            break
        path = path + '/tmms'
        make_symlink(git_repo_path, path)
    else:
        raise RuntimeError(
            'Can\'t find suitable path in python environment to link tmms!')


def link_into_usrlocalbin(args, git_repo_path):
    """
        Create a symlink to THIS manifesting source tree tm_cmd for
    /usr/local/bin/tm-manifest as specified by ERS.
    """
    symlink_path = '/usr/local/bin/'
    if not os.path.exists('%s/tm-manifest' % (symlink_path)):
        make_symlink(
            git_repo_path + '/tm_cmd/tm_manifest.py',
            '/usr/local/bin/tm-manifest')
    elif args.verbose:
        print('%s/tm-manifest already exists' % (symlink_path))

    if not os.path.exists('%s/tm-manifest-server' % (symlink_path)):
        make_symlink(
            git_repo_path + '/manifest_api.py',
            '/usr/local/bin/tm-manifest-server')
    elif args.verbose:
        print('%s/tm-manifest-server already exists' % (symlink_path))


def try_dh_helper(argv):
    '''If the directive is a dh_helper keyword, process this and EXIT.'''
    legal = ('clean', 'install', 'build')
    if not argv or argv[0] not in legal:
        return
    raise SystemExit()


def parse_cmdline_args(extra_args_msg):
    '''There are no import dependencies here.'''

    config = '/etc/tmms'
    if not os.path.isfile(config):  # Use the sample supplied with repo
        config = os.path.dirname(os.path.realpath(__file__)) + '/tmms'
    assert os.path.isfile(config), 'This is very bad'

    parser = argparse.ArgumentParser(
        description='Setup arguments intended for tmms developers only')
    parser.add_argument(
        '-c', '--config',
        help='Configuration file to be used.\nDefault=%s' % config,
        default=config)

    parser.add_argument(
        '--auto-update',
        help='Let flask serve auto restart on code change',
        action='store_true')
    parser.add_argument(
        '-D', '--daemon-start',
        help='Run as a daemon process.',
        action='store_true')
    parser.add_argument(
        '--daemon-stop',
        help='Stop the daemon',
        action='store_true')
    parser.add_argument(
        '--daemon-status',
        help='Print status of the daemon',
        action='store_true')
    parser.add_argument(
        '--daemon-restart',
        help='Restart the daemon',
        action='store_true')
    parser.add_argument(
        '--start-dnsmasq',
        help='Only (re)start dnsmasq and exit',
        action='store_true')

    parser.add_argument(
        '--debug',
        help='Turn on flask debugging.',
        action='store_true')
    parser.add_argument(
        '--dry-run',
        help='No action; simulation of events.',
        action='store_true')
    parser.add_argument(
        '-P', '--packaging',
        help='This flag should only be set by post-setup scripts in Debian ' +
             'installer. Using it while trying to run from the git repo ' +
             'will result in a non-functioning environment.\n',
        action='store_true')
    parser.add_argument(
        '-v', '--verbose',
        help='Make me talk more.',
        action='store_true')
    parser.add_argument(
        'extra', nargs='*',
        help=extra_args_msg,
        default=())
    args = parser.parse_args()

    assert os.geteuid() == 0, 'You must be root'    # after parse check
    if args.debug:
        args.verbose = True     # this is what forces logging at DEBUG level
    return args


if __name__ == '__main__':
    try:
        assert 'linux' in sys.platform, 'I see no Tux here (%s)' % sys.platform
        args = parse_cmdline_args(
            'setup action(s):\n   "all", "environment", "networking", "golden_image"')
        try_dh_helper(args.extra)     # Doesn't return if packaging called me

        # Imports are relative because implicit Python path "tmms" may not
        # exist yet.  I think this will break if run from configs?  Anyhow,
        # this script needs to do a few things that Debian postinstall
        # scripts will do.
        try:
            from utils.file_utils import make_symlink
        except ImportError:
            raise SystemExit('Failed to import utils.file_utils module')

        setup_file = os.path.realpath(__file__)
        git_repo_path = os.path.dirname(setup_file)
        link_into_python(args, git_repo_path)
        link_into_usrlocalbin(args, git_repo_path)

        legal = ('environment', 'networking', 'golden_image')  # order matters
        if not args.extra or 'all' in args.extra:
            actions = legal
        else:
            assert args.extra[0] in legal, 'Illegal action "%s"' % a
            actions = args.extra
        for a in actions:
            if a == 'environment':
                from configs import setup_environment
                setup_environment.main(args)
            elif a == 'networking':
                from configs import setup_networking
                setup_networking.main(args)
            elif a == 'golden_image':
                from configs import setup_golden_image
                setup_golden_image.main(args)
        raise SystemExit(0)
    except ImportError as err:
        errmsg = 'import failed: %s\nTry "setup.py all" or "setup.py environment"' % str(err)
    except (AssertionError, RuntimeError, ValueError) as err:
        errmsg = str(err)
    except NameError as err:
        errmsg = 'Name (coding) error: line %d: %s' % (
            sys.exc_info()[2].tb_lineno, str(err))
    except RuntimeError as err:
        errmsg = 'Stay calm. We just caught an error duing the install process! [%s]' % err
    except Exception as err:
        errmsg = 'UNEXPECTED ERROR: line %d: %s' % (
            sys.exc_info()[2].tb_lineno, str(err))

    raise SystemExit('%s\nsetup failed' % errmsg)
