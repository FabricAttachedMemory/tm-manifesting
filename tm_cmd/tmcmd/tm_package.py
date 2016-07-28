#!/usr/bin/python3 -tt
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
    SYNOPSIS
        listpkgs

    DESCRIPTION
        List all the packages available in the repo with its metadata in json
    string format.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'packages/')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, target, **options):
        """
    SYNOPSIS
        showpkg <name>

    DESCRIPTION
        List metadata of the package in json string format.
        """
        super().show(target, **options)
        url = "%s%s%s" % (self.url, 'package/', self.show_name)
        data = self.http_request(url)
        return self.to_json(data)