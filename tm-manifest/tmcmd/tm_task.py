#!/usr/bin/python3 -tt

from pdb import set_trace

from . import tm_base


class TmTask(tm_base.TmCmd):

    def __init__(self):
        """
            Define 'args' for this class.
        """
        super().__init__()
        self.args = {
            'listtasks' : self.listtasks,
            'showtask' : self.showtask
        }


    def listtasks(self, args, **options):
        """
    SYNOPSIS
        listtasks [verbose | debug]

    DESCRIPTION
        List all tasks present in the service in json string format.
        """
        assert len(args) == 0, '"listtasks" does not take non-optional arguments!'
        url = "%s%s" % (self.url, 'task/')

        if options['verbose']:
            print(' - "listtasks" sending request to "%s"...' % url)
        if options['debug']:
            set_trace()

        data = self.http_request(url)
        return self.to_json(data)


    def showtask(self, args, **options):
        """
    SYNOPSIS
        showtask <name> [verbose | debug]

    DESCRIPTION
        List all the packages defined by a task in json string format.
        """
        assert len(args) >= 1, 'Missing argument: showtask <name>!'
        name = args[0]
        url = "%s%s%s" % (self.url, 'task/', name)

        if options['verbose']:
            print(' - "showtask" sending request to "%s"...' % url)
        if options['debug']:
            set_trace()

        data = self.http_request(url)
        return self.to_json(data)
