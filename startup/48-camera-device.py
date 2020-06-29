
from BMM.camera_device import BMMSnapshot

run_report(__file__, text='web and analog cameras as devices captured by DataBroker')

xascam = BMMSnapshot(root='/nist/xf06bm/experiments/XAS/snapshots', which='XAS',    name='xascam')
xrdcam = BMMSnapshot(root='/nist/xf06bm/experiments/XAS/snapshots', which='XRD',    name='xrdcam')
anacam = BMMSnapshot(root='/nist/xf06bm/experiments/XAS/snapshots', which='analog', name='anacam')

## the output file names is hidden away in the dict returned by this: a.describe()['args']['get_resources']()
#
# a=db.v2[-1] 
#
# BMM XRD.111 [8] ▶ a.describe()['args']['get_resources']()[0]['root']                                                                                  
# Out[8]: '/nist/xf06bm/experiments/XAS/snapshots'
#
# BMM XRD.111 [9] ▶ a.describe()['args']['get_resources']()[0]['resource_path']                                                                         
# Out[9]: '17f7c1e0-6796-49da-95aa-c3f2ccc3d5ca_%d.jpg'

# img=db.v2[-1].primary.read()['anacam_image']
# this gives a 3D array, [480,640,3], where the 3 are RGB values 0-to-255
# how to export this as a jpg image???


def fetch_snapshot(record):
    '''Return the fully resolved path to the filestore image collected by a BMMSnapshot device'''
    if 'databroker.core.BlueskyRunFromGenerator' in str(type(record)) :
        #template = os.path.join(record.describe()['args']['get_resources']()[0]['root'],
        #                        record.describe()['args']['get_resources']()[0]['resource_path'])
        #return(template % 0)
        return(None)
    elif 'databroker.core.BlueskyRun' in str(type(record)) :
        template = os.path.join(record.describe()['args']['get_resources']()[0]['root'],
                                record.describe()['args']['get_resources']()[0]['resource_path'])
        return(template % 0)
    else:
        return(None)



import BMM.camera_device

def snap(which, filename=None, **kwargs):
    if which is None: which = 'XAS'
    if which.lower() == 'xrd':
        BMM.camera_device.xrd_webcam(filename=filename, **kwargs)
    elif 'ana' in which.lower() :
        BMM.camera_device.analog_camera(filename=filename, **kwargs)
    else:
        BMM.camera_device.xas_webcam(filename=filename, **kwargs)
    
