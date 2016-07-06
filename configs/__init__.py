import os

from pdb import set_trace

PYTHONPATH_CFG = os.path.realpath(__file__)
PYTHONPATH_CFG = os.path.dirname(PYTHONPATH_CFG)
PYTHONPATH_CFG = os.path.join(PYTHONPATH_CFG,'tmms.pth')
