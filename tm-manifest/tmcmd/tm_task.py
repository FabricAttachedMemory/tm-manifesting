#!/usr/bin/python3 -tt

from pdb import set_trace

from . import tm_base


class TmTask(tm_base.TmCmd):
    """
        A class that handles 'tasks' of the manifesting API.
    """
    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listtasks' : self.listall,
            'showtask' : self.show
        }


    def listall(self, arg_list=None, **options):
        """
    SYNOPSIS
        listtasks [verbose | debug]

    DESCRIPTION
        List all tasks present in the service in json string format.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'task/')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, target, **options):
        """
    SYNOPSIS
        showtask <name> [verbose | debug]

    DESCRIPTION
        List all the packages defined by a task in json string format.
        """
        super().show(target, **options)
        url = "%s%s%s" % (self.url, 'task/', self.show_name)
        data = self.http_request(self.url)
        return self.to_json(data)





    # def listtasks(self, args=[], **options):
    #     """
    # SYNOPSIS
    #     listtasks [verbose | debug]
    #
    # DESCRIPTION
    #     List all tasks present in the service in json string format.
    #     """
    #     assert len(args) == 0, '"listtasks" does not take non-optional arguments!'
    #     url = "%s%s" % (self.url, 'task/')
    #
    #     if 'verbose' in options and options['verbose']:
    #         print(' - "listtasks" sending request to "%s"...' % url)
    #
    #     data = self.http_request(url)
    #     return self.to_json(data)
    #
    #
    # def showtask(self, args, **options):
    #     """
    # SYNOPSIS
    #     showtask <name> [verbose | debug]
    #
    # DESCRIPTION
    #     List all the packages defined by a task in json string format.
    #     """
    #     assert len(args) >= 1, 'Missing argument: showtask <name>!'
    #     # Let user pass both types to avoid confusion passing args as "list" for a single argument.
    #     #Passing list is helpfull for a generic function call, like it used in tm_manifest.py
    #     name = args[0] if type(args) is list else args
    #     url = "%s%s%s" % (self.url, 'task/', name)
    #
    #     if 'verbose' in options and options['verbose']:
    #         print(' - "showtask" sending request to "%s"...' % url)
    #
    #     data = self.http_request(url)
    #     return self.to_json(data)
