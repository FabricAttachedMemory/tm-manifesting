"""
    Import templates/grub/ as a module in your script to get all the templates
of in this category already parsed and saved in the appropriate variables:
    grub_menu - a template for grub_menu.template
"""
import os
from jinja2 import Environment, FileSystemLoader

from pdb import set_trace

path_to_templates = os.path.realpath(__file__)
path_to_templates = os.path.dirname(path_to_templates)
_jinja_env = Environment(loader=FileSystemLoader(path_to_templates))
_jinja_env.trim_blocks = True
grub_menu = _jinja_env.get_template('grub_menu.template')
