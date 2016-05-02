#!/usr/bin/python3 -tt

def overwrite_file_content(target, content, **options):
        """ 
                Overwrite file in the targeted location with a new content.

                    :param 'target': [str] path to a file to create or overwrite with a new content
                        :param 'content': [str] content to use in the new\overwritten file.
                            :param 'verbose': [bool] Make it talk.
                                """
                                    with open(target, 'w+') as file_obj:
                                                if options.get('verbose', False):
                                                                print ('Writing into "%s": \n[\n%s\n]\n' % (target, content))
                                                                        file_content = '%s\n' % str(content)
                                                                                file_obj.write(file_content)
