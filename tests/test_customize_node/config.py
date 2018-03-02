#!/usr/bin/python3 -tt
import os
import sys
#customize_node = os.path.realpath(__file__)
#customize_node = os.path.dirname(customize_node)
#customize_node = '%s/../../blueprints/30-nodes/node_builder/' % (customize_node)
#sys.path.append(customize_node)
from tmms.utils import customize_node as CN

tmp_folder = "/tmp/UNITTEST_CUSTOMNODE"
fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img"


def setup():
    """
        Emulare a filesystem image in the tmp directory with only those folders
    and files that are manipulated by customize_node.py script.
    """
    if os.path.isdir(tmp_folder):
        rmtree(tmp_folder)
    if os.path.isdir(fs_img):
        rmtree(fs_img)
    os.makedirs(tmp_folder)
    os.makedirs(fs_img)

    fs_dirtree = ['boot/', 'etc/', 'etc/apt/sources.list.d/', 'sbin/']
    # FIXME: hardcoded constants have to be kept in sync in two files
    fs_files = ['boot/initrd.img-4.5.0-3-arm64-l4tm-tmas',
                'boot/vmlinuz-4.5.0-3-arm64-l4tm-tmas',
                'etc/hosts',
                'etc/hostname',
                'sbin/init',
                'etc/apt/sources.list']

    for fs_dirname in fs_dirtree:
        os.makedirs('%s/%s' % (fs_img, fs_dirname))

    for fs_file in fs_files:
        file_path = '%s/%s' % (fs_img, fs_file)
        with open(file_path, 'a') as file_obj:
            os.utime(file_path, None)
