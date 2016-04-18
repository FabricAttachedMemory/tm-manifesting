#!/usr/bin/python3 -tt
from pdb import set_trace

class Blueprint():

    def __init__(self, cfg={}, BP=None):
        self.data = {}
        self.config = cfg
        # if type(BP) is not flask.blueprints.Blueprint:
        #     warnings.warn('BP variable sent to a constructor is not of type "flask.blueprints.Blueprint"!')
        # else:
        #     BP.filter = self.filter_out

    def load_data(self):
        """
            TODO: Docstr
        """
        return NotImplementedError('Ouch!')


    def update(self, to_update):
        """
            Update class dictionary with a passed list of dicts.
        """
        # self.data.update(dict((task['Task'], task) for task in tmp))
        for dict_obj in tmp:
            for key, val in dict_obj.items():
                self.data.update(key, val)


    def open_file(self, target):
        with open(target, 'r') as file_obj:
            return file_obj.read()


    def filter_out(self, target_list):
        """
            Get list of objects that are not in the class dictionary.
        :self 'target_list': [list] of objects to filter out from class dictionary.
        :return: [list] of objects that are not found in the class dictionary.
        """
        return [ target for target in target_list if target not in self.data ]


    def lookup(self, search_key, return_val=None):
        """
            Get value from the data for the given key.
        Return None(by default) if key not found.
        :param 'key': [str] key name to find value for in the class dictionary.
        :param 'return_val': [any](default=None) return value if key not found. (can be sub/path/name)
        :return: [any] value stored in the class dictionary associated with the key.
        """
        # set_trace()
        return self.data.get(search_key, return_val)


    def jasonify(self):
        raise NotImplementedError("Beem! Bam! Bosh!")


    @property
    def keys(self):
        """ Return keys of self.data """
        return self.data.keys()
