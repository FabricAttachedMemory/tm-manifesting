#!/usr/bin/python3 -tt
"""
    Test set of functions that are responsible for filesystem image customization,
e.g. kernel cleanup, fixing init and etc.
"""

import os
import shlex
import sys
import unittest
from shutil import rmtree, copytree
tomize_node = os.path.realpath(__file__)
customize_node = os.path.dirname(customize_node)
customize_node = '%s/../blueprints/30-nodes/node_builder/' % (customize_node)
sys.path.append(customize_node)
import customize_node as CN


class PackageTest
