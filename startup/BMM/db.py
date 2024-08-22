import os, re
import numpy
import matplotlib.pyplot as plt

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

def file_resource(record):
    '''Return the fully resolved path to the data resource associated with
    the record, e.g.

    - the filestore image collected by a BMMSnapshot device 
    - the HDF5 file associated with an XRF measurement or a 
      fluorescence XAFS scan

    Argument is either a uid string or Tiled catalog.

    Anything that cannot be interpreted to return a path will return None.

    '''
    if type(record) is str:
        try:
            record = user_ns['bmm_catalog'][record]
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
    elif 'databroker.client.BlueskyRun' in str(type(record)):
        docs = record.documents()
        for d in docs:
            if d[0] == 'resource':
                this = os.path.join(d[1]['root'], d[1]['resource_path'])
                if '_%d' in this or re.search('%\d\.\dd', this) is not None:
                    this = this % 0
                return(this)
    else:
        return(None)

import matplotlib.pyplot as plt
def show_snapshot(uid):
    '''Quickly plot a snapshot image from DataBroker given its UID.
    '''
    if 'usbcam-1_image' in user_ns['bmm_catalog'][uid]['primary']['data']:
        plt.imshow(user_ns['bmm_catalog'][uid]['primary']['data']['usbcam-1_image'][0,:])
    elif 'usbcam-2_image' in user_ns['bmm_catalog'][uid]['primary']['data']:
        plt.imshow(user_ns['bmm_catalog'][uid]['primary']['data']['usbcam-2_image'][0,:])        
    else:                       # pre-data-security
        this = user_ns['bmm_catalog'][uid].primary.read()
        if 'usbcam1_image' in this:
            key = 'usbcam1_image'
        elif 'usbcam2_image' in this:
            key = 'usbcam2_image'
        elif 'xascam_image' in this:
            key = 'xascam_image'
        elif 'anacam_image' in this:
            key = 'anacam_image'
        plt.imshow(numpy.array(this[key])[0])
    plt.grid(False)
