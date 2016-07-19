#!/usr/bin/python3

from distutils.core import setup

setup(name='tm-manifest',
    version='0.5',
    description='TM-Manifesting solution.',
    author='Zach Volchak',
    author_email='zakhar.volchak@hpe.com',
    url='https://github.hpe.com/hpelinux/manifesting.git',
    packages=['tm_manifest'],
    package_dir= {'tmms', 'tftp'},
    ext_modules=[Extenstion(
                'suite_config',['unittests/suite_config.py'],
                'tmcmd', ['tm-manifest/']
                )]
