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
        url = "%s%s" % (self.url, 'tasks/')
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
        url_to_task = "%s%s%s" % (self.url, 'task/', self.show_name)
        data = self.http_request(url_to_task)
        return self.to_json(data)
