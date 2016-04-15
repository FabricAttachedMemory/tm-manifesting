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
            'listpkgs' : self.listpkgs,
            'showpkg' : self.showpkg
        }


    def listpkgs(self, *args, **options):
        """
    SYNOPSIS
        listpkgs

    DESCRIPTION
        List all the packages available in the repo with its metadata in json
    string format.
        """
        url = "%s%s" % (self.url, 'package/')
        data = self.http_request(url)
        return self.to_json(data)


    def showpkg(self, args, **options):
        """
    SYNOPSIS
        showpkg <name>

    DESCRIPTION
        List metadata of the package in json string format.
        """
        try:
            name = args[0]
        except IndexError:
            return { "error" : "missing package name in function call!" }
        url = "%s%s%s" % (self.url, 'package/', name)
        data = self.http_request(url)
        return self.to_json(data)
