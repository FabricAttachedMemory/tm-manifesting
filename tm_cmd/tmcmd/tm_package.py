#!/usr/bin/python3 -tt
"""
  This class inherits from tm_base.py class and is used to handle "packages"
related operations, such as list and getting metadata of available packages based
of the Mirror set in the tmms config.
"""
__author__ = "Zakhar Volchak, Rocky Craig"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Zakhar Volchak, Rocky Craig"
__email__ = "zach.bender@tutanota.com, rocky.craig@hpe.com"


from pdb import set_trace
from . import tm_base

class TmPackage(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listpkgs' : self.listall,
            'showpkg' : self.show
        }

    def listall(self, arg_list=None, **options):
        """
        listpkgs

        List all the packages available in the repo with its metadata in JSON.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'packages/')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, target, **options):
        """
        showpkg <name>

        List metadata of the package in JSON format.
        """
        super().show(target, **options)
        url = "%s%s%s" % (self.url, 'package/', self.show_name)
        data = self.http_request(url)
        return self.to_json(data)
