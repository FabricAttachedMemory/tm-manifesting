#!/usr/bin/python3
import os
from distutils.core import setup, Extension

setup(name='tm-manifest',
    version='0.5',
    description='TM-Manifesting solution.',
    author='Zach Volchak',
    author_email='zakhar.volchak@hpe.com',
    url='https://github.hpe.com/hpelinux/manifesting.git',
    packages=['.', 'tm-manifest', 'tm-manifest/tmcmd/']
    #package_dir= {'' : 'blueprints/30-nodes/' }
    #ext_modules=[Extension('suite_config',['unittests/suite_config.py'],
    #            'tmcmd', ['tm-manifest/'])
    #            ],
    #data_files = [ ('/etc/' , ['configs/hpetmconfig.json']) ]
    #data_files = [ ('', ['blueprints/*']) ]
    )

from pdb import set_trace

def find_all():
    for root, dirs, files in os.walk('blueprints/'):
        for name in files:
            if name.endswith('.py'):
                print(os.path.join(root, name))
#        for name in dirs:
#            print(os.path.join(root, name))

find_all()
