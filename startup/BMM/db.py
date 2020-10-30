import os

from bluesky_queueserver.manager.profile_tools import set_user_ns

## from IPython import get_ipython
## user_ns = get_ipython().user_ns


@set_user_ns
def file_resource(record, user_ns):
    '''Return the fully resolved path to the filestore image collected by a BMMSnapshot device

    Argument is either a uid string or db.v2 (databroker.core.BlueskyRun) object.

    Anything that cannot be interpreted to return a path will return None.
    '''
    if type(record) is str:
        try:
            record = user_ns['db'].v2[record]
        except:
            return(None)
    if 'databroker.core.BlueskyRunFromGenerator' in str(type(record)) :
        #template = os.path.join(record.describe()['args']['get_resources']()[0]['root'],
        #                        record.describe()['args']['get_resources']()[0]['resource_path'])
        #return(template % 0)
        return(None)
    elif 'databroker.core.BlueskyRun' in str(type(record)) :
        template = os.path.join(record.describe()['args']['get_resources']()[0]['root'],
                                record.describe()['args']['get_resources']()[0]['resource_path'])
        try:
            return(template % 0)
        except:
            return(template)
    else:
        return(None)

        
