#!/usr/bin/python3 -tt
"""
    Test set of functions that are responsible for filesystem image customization,
e.g. kernel cleanup, fixing init and etc.
"""
from pdb import set_trace

import os
import shlex
import sys
import unittest
from shutil import rmtree, copytree
customize_node = os.path.realpath(__file__)
customize_node = os.path.dirname(customize_node)
customize_node = '%s/../blueprints/30-nodes/node_builder/' % (customize_node)
sys.path.append(customize_node)
import customize_node as CN


class CustomizeNodeRoutineTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/"
    fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img/"

    @classmethod
    def setUp(cls):
        """
            Emulare a filesystem image in the tmp directory with only those folders
        and files that are manipulated by customize_node.py script.
        """
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)
        if os.path.isdir(cls.fs_img):
            rmtree(cls.fs_img)
        os.makedirs(cls.tmp_folder)
        os.makedirs(cls.fs_img)

        fs_dirtree = ['boot/', 'etc/', 'etc/apt/sources.list.d/', 'sbin/']
        fs_files = ['boot/initrd.img-4.3.0-3-arm64-l4tm',
                    'boot/vmlinuz-4.3.0-3-arm64-l4tm',
                    'etc/hosts',
                    'etc/hostname',
                    'sbin/init',
                    'etc/apt/sources.list']

        for fs_dirname in fs_dirtree:
            os.makedirs('%s/%s' % (cls.fs_img, fs_dirname))

        for fs_file in fs_files:
            file_path = '%s/%s' % (cls.fs_img, fs_file)
            with open(file_path, 'a') as file_obj:
                os.utime(file_path, None)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)


    def test_cleanout_kernel(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to move boot/ files into tmp directory using customize_node.cleanout_kernel
        function.
        """
        CN.cleanout_kernel(self.fs_img, self.tmp_folder)
        boot_files = ['initrd.img-4.3.0-3-arm64-l4tm',
                      'vmlinuz-4.3.0-3-arm64-l4tm']
        for boot_file in boot_files:
            boot_old = '%s/boot/%s' % (self.fs_img, boot_file)
            boot_new = '%s/%s' % (self.tmp_folder, boot_file)
            self.assertFalse(os.path.exists(boot_old),
                    '"%s" should have been removed!' % (boot_old))
            self.assertTrue(os.path.exists(boot_new),
                            '"%s" was not found!' % (boot_new))


    def test_cleanout_kernel_exception(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to move boot/ files into tmp directory using customize_node.cleanout_kernel
        function. In this test we are trying to catch and error, thus, the boot
        files will not exist, so that the RuntimeError will be thrown.
        """
        boot_dir = '%s/boot/' % self.fs_img
        rmtree(boot_dir)
        self.assertFalse(os.path.isdir(boot_dir), 'Couldn\'t remove boot/!')

        self.assertRaises(RuntimeError, CN.cleanout_kernel(self.fs_img, self.tmp_folder),
                'Unexpected error was raised!')


    def test_fix_init(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to create a symbolic link from fs_img/sbin/init into fs_img/init.
        """
        CN.fix_init(self.fs_img)
        new_init = '%s/init' % self.fs_img

        self.assertTrue(os.path.exists(new_init),
                'Symlink to "%s" was not created!' % new_init)

        CN.fix_init(self.fs_img)
        self.assertTrue(os.path.exists(new_init),
                'Recreating symlink to "%s" faild! Couldn\'t remove old init!' % new_init)


    def test_fix_init_exception(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to create a symbolic link from fs_img/sbin/init into fs_img/init. This
        time, we will try to catch a RuntimeError exception, by removing init
        file before creating a symlink.
        """
        orig_init = '%s/sbin/init' % self.fs_img
        os.remove(orig_init)
        self.assertRaises(RuntimeError, CN.fix_init(self.fs_img),
                'Unexpected error was raised!')
        wrong_fsimg = '/tmp/'
        try:
            CN.fix_init(wrong_fsimg)
            self.assertTrue(False, 'Should have faild due to a wrong fsimg path')
        except RuntimeError:
            self.assertTrue(True)


    def test_cleanup_sources_list(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        fix sources.list and sources.list.d/base.list using customize_node.cleanup_sources_list
        function, e.g. move content of base.list into sources.list and removing base.list file.
        """
        sourceslist_file = '%s/etc/apt/sources.list' % self.fs_img
        baselist_file = '%s/etc/apt/sources.list.d/base.list' % self.fs_img
        CN.cleanup_sources_list(self.fs_img)

        self.assertFalse(os.path.exists(baselist_file),
                        'base.list file was not removed!')
        self.assertTrue(os.path.exists(sourceslist_file),
                    'What happened to sources.list file? Where is it off to?')
        self.assertIsNone(CN.cleanup_sources_list(self.fs_img), 'base.list still exists?')


    def test_set_hostname(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to set a custom name to etc/hostname using customize_node.set_hostname
        function.
        """
        hostname_test = 'Abyss'
        hostname_file = '%s/etc/hostname' % self.fs_img

        CN.set_hostname(self.fs_img, hostname_test)
        hostname_new = None
        with open(hostname_file, 'r') as file_obj:
            hostname_new = file_obj.read()
        self.assertTrue(hostname_test in hostname_new,
                'Hostname was not set to "%s"!' % hostname_test)


    def test_set_hosts(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        """
        hosts_file = '%s/etc/hosts' % self.fs_img
        hostname = 'Abyss'

        CN.set_hosts(self.fs_img, hostname)

        hosts_new = None
        with open(hosts_file, 'r') as file_obj:
            hosts_new = file_obj.read()

        localhost_line = '127.0.0.1   localhost'
        hostname_line = '127.1.0.1   %s' % hostname
        self.assertTrue(localhost_line in hosts_new, '"%s" is not in etc/hosts!' % localhost_line)
        self.assertTrue(hostname_line in hosts_new, '"%s" is not in etc/hosts!' % hostname_line)


    #TODO: Test customize_node.untar


    def test_create_cpio(self):
        """
        """
        cpio_file = '%s/fs_img.cpio' % self.tmp_folder
        CN.create_cpio(self.fs_img, cpio_file)
        self.assertTrue(os.path.exists(cpio_file), 'cpio file was not created!')


    #TODO: Test create_cpio exceptions


if __name__ == '__main__':
    unittest.main()
