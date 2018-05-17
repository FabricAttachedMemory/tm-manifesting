#!/usr/bin/python3 -tt
"""
  This class inherits from tm_base.py class and is used to handle "tasks" related
operations, such as list and get description of available tasks to use for image
building process.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"

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
        listtasks [verbose | debug]

        List all tasks present in the service in json string format.
        """
        super().listall(arg_list, **options)
        url = "%s%s" % (self.url, 'tasks/')
        data = self.http_request(url)
        return self.to_json(data)


    def show(self, target, **options):
        """
        showtask <name> [verbose | debug]

        List all the packages defined by a task in JSON format.
        """
        super().show(target, **options)
        url_to_task = "%s%s%s" % (self.url, 'task/', self.show_name)
        data = self.http_request(url_to_task)
        return self.to_json(data)
