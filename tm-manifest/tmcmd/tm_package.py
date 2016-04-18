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

    def listall(self, *args, **options):
        """
    SYNOPSIS
        listpkgs

    DESCRIPTION
        List all the packages available in the repo with its metadata in json
    string format.
        """
        super().listall(args=args, option=options)
        url = "%s%s" % (self.url, 'package/')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, args, **options):
        """
    SYNOPSIS
        showpkg <name>

    DESCRIPTION
        List metadata of the package in json string format.
        """
        super().show(args=args, option=options)
        url = "%s%s%s" % (self.url, 'package/', self.show_name)
        data = self.http_request(url)
        return self.to_json(data)


    # def listpkgs(self, *args, **options):
    #     """
    # SYNOPSIS
    #     listpkgs
    #
    # DESCRIPTION
    #     List all the packages available in the repo with its metadata in json
    # string format.
    #     """
    #     assert len(args) == 0, '"listpkgs" does not take non-optional arguments!'
    #     if 'verbose' in options and options['verbose']:
    #         print(' - "listpkgs" sending request to "%s"...' % url)
    #
    #     url = "%s%s" % (self.url, 'package/')
    #     data = self.http_request(url)
    #     return self.to_json(data)



    # def showpkg(self, args, **options):
    #     """
    # SYNOPSIS
    #     showpkg <name>
    #
    # DESCRIPTION
    #     List metadata of the package in json string format.
    #     """
    #     assert len(args) >= 1, 'Missing argument: args <name>!'
    #     # Let user pass both types to avoid confusion passing args as "list" for a single argument.
    #     #Passing list is helpfull for a generic function call, (as in tm_manifest.py)
    #     name = args[0] if type(args) is list else args
    #     if 'verbose' in options and options['verbose']:
    #         print(' - "showpkg" sending request to "%s"...' % url)
    #
    #     url = "%s%s%s" % (self.url, 'package/', name)
    #     data = self.http_request(url)
    #     return self.to_json(data)
