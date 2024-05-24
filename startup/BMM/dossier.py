import os, re, socket
from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter
from urllib.parse import quote
import numpy

from bluesky.plans import count
from bluesky.plan_stubs import sleep, mv, null

import matplotlib
import matplotlib.pyplot as plt
from larch.io import create_athena

from PIL import Image

from BMM.db                import file_resource
from BMM.functions         import error_msg, bold_msg, whisper, plotting_mode, now, proposal_base
from BMM.kafka             import kafka_message
from BMM.logging           import report
from BMM.modes             import get_mode, describe_mode
from BMM.periodictable     import edge_energy, Z_number, element_name

from BMM.user_ns.base      import bmm_catalog
from BMM.user_ns.dwelltime import use_4element, use_1element

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False


def lims(toggle='on'):
    if toggle == 'off':
        user_ns['BMMuser'].lims      = False
        user_ns['BMMuser'].snapshots = False
        user_ns['BMMuser'].htmlout   = False
    else:
        user_ns['BMMuser'].lims      = True
        user_ns['BMMuser'].snapshots = True
        user_ns['BMMuser'].htmlout   = True
        
    
class DossierTools():
    '''A class for aiding in generation of a static HTML file for
    documenting an XAS measurement at BMM.  Most of the work of
    dossier generation is done by the file_management kafka client.
    This class is used to organize ancillary measurements, like camera
    snapshots and XRF spectra measurement.

    attributes
    ==========
    pccenergy : float
      the energy at which the mono was put into pseudo-channel-cut mode
    websnap : str
      the filename of the image from the XAS webcam
    webuid : str
      the UID of the XAS webcam exposure
    anasnap : str
      the filename of the image from the analog pinhole camera
    anauid : str
      the UID of the analog pinhole camera exposure
    usb1snap : str
      the filename of the image from the first USB webcam
    usb1uid : str
      the UID of the first USB camera exposure
    usb2snap : str
      the filename of the image from the second USB camera
    usb2uid : str
      the UID of the second USB camera exposure
    xrfsnap : str
      the filename of the XRF image
    xrffile : str
      the filename of the XRF data
    xrfuid : str
      the UID of the Xspress3 XRF webcam exposure
    ocrs : str
      stringification of the OCR values from the XRF exposure
    rois : str
      stringification of the ROI values from the XRF exposure

    methods
    =======
    capture_xrf
      measure an XRF spectrum and capture its metadata for use in a dossier

    cameras
      take a snapshot with each camera and capture metadata for use in a dossier

    instrument state
    ================

    (This is useful, but needs to be captured somewhere else.)

    If using one of the automated instruments (sample wheel, Linkam
    stage, LakeShore temperature controller, glancing angle stage,
    motor grid), the class implementing the instrument is responsible
    for supplying a method called dossier_entry.  Here is an example
    from the glancing angle stage class:

           def dossier_entry(self):
              thistext  =  '	    <div>\n'
              thistext +=  '	      <h3>Instrument: Glancing angle stage</h3>\n'
              thistext +=  '	      <ul>\n'
              thistext += f'               <li><b>Spinner:</b> {self.current()}</li>\n'
              thistext += f'               <li><b>Tilt angle:</b> {xafs_pitch.position - self.flat[1]:.1f}</li>\n'      
              thistext += f'               <li><b>Spinning:</b> {"yes" if self.spin else "no"}</li>\n'
              thistext +=  '	      </ul>\n'
              thistext +=  '	    </div>\n'
              return thistext

    This returns a <div> block for the HTML dossier file.  The
    contents of this text include a header3 description of the
    instrument and an unordered list of the most salient aspects of
    the current state of the instrument.

    Admittedly, requiring a method that generates suitable HTML is a
    bit unwieldy, but is allows much flexibility in how the instrument
    gets described in the dossier.

    The dossier_entry methods get used in BMM/xafs.py around line 880.

    The methods raster_dossier and sead_dossier serve this purpose for
    those measurements.

    '''
    xrf_md        = {}
    cameras_md    = {}
    websnap       = ''
    webuid        = ''
    anasnap       = ''
    anauid        = ''
    usb1snap      = ''
    usb1uid       = ''
    usb2snap      = ''
    usb2uid       = ''
    xrfsnap       = ''
    xrffile       = ''
    xrfuid        = ''
    ocrs          = ''
    rois          = ''

    npoints       = 0
    dwell         = 0
    delay         = 0
    scanuid       = None
    
    def __init__(self):
        self.scanlist      = ''

    def capture_xrf(self, folder, stub, mode, md):
        '''Capture an XRF spectrum and related metadata at the current energy
        '''
        
        BMMuser, xs, xs1, dcm = user_ns['BMMuser'], user_ns['xs'], user_ns['xs1'], user_ns['dcm']

        thisagg = matplotlib.get_backend()
        matplotlib.use('Agg') # produce a plot without screen display
        ahora = now()
        self.xrffile = "%s_%s.xrf" % (stub, ahora)
        self.xrfsnap = "%s_XRF_%s.png" % (stub, ahora)
        #xrffile  = os.path.join('XRF', self.xrffile)
        #xrfimage = os.path.join('XRF', self.xrfsnap)
        md['_xrffile']  = self.xrffile
        md['_xrfimage'] = self.xrfsnap
        md['_pccenergy'] = f'{dcm.energy.position:.2f}'
        md['_user'] = dict()
        md['_user']['startdate'] = BMMuser.date
        if use_4element and plotting_mode(mode) == 'xs':
            report(f'measuring an XRF spectrum at {dcm.energy.position:.1f} (4-element detector)', 'bold')
            yield from mv(xs.total_points, 1)
            yield from mv(xs.cam.acquire_time, 1)
            self.xrfuid = yield from count([xs], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata XRF'})
            
        if use_1element and plotting_mode(mode) == 'xs1':
            report(f'measuring an XRF spectrum at {dcm.energy.position:.1f} (1-element detector)', 'bold')
            yield from mv(xs1.total_points, 1)
            yield from mv(xs1.cam.acquire_time, 1)
            self.xrfuid = yield from count([xs1], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata XRF'})

        kafka_message({'xrf' : 'plot',
                       'uid' : self.xrfuid,
                       'add' : False,
                       'filename' : self.xrfsnap,
                       'post' : BMMuser.post_xrf, })
        kafka_message({'xrf' : 'write',
                       'uid' : self.xrfuid,
                       'filename' : self.xrffile, })

        ## capture OCR and target ROI values at Eave to report in dossier
        #self.ocrs = ", ".join(map(str,ocrs))
        #self.rois = ", ".join(map(str,rois))

        ### --- capture metadata for dossier -----------------------------------------------
        self.xrf_md = {'xrf_uid'   : self.xrfuid, 'xrf_image': self.xrfsnap,}
                       
        

    def cameras(self, folder, stub, md):
        '''For each camera in use at the beamline, capture and image and record relevant
        metadata (UID, filename) for dossier creation
        '''
        ahora = now()
        BMMuser, xascam, anacam, usbcam1, usbcam2 = user_ns['BMMuser'], user_ns['xascam'], user_ns['anacam'], user_ns['usbcam1'], user_ns['usbcam2']
        image_ana, image_web, image_usb1, image_usb2 = '','','',''
        
        ### --- XAS webcam ---------------------------------------------------------------
        annotation = stub
        websnap = "%s_XASwebcam_%s.jpg" % (stub, ahora)
        image_web = os.path.join(folder, 'snapshots', websnap)
        md['_filename'] = image_web
        xascam._annotation_string = annotation
        print(bold_msg('XAS webcam snapshot'))
        webuid = yield from count([xascam], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
        self.websnap, self.webuid = websnap, webuid
        #yield from sleep(0.5)
        #im = Image.fromarray(numpy.array(bmm_catalog[webuid].primary.read()['xascam_image'])[0])
        #im.save(image_web, 'JPEG')
        kafka_message({'copy': True,
                       'file': file_resource(webuid),
                       'target': os.path.join(proposal_base(), 'snapshots', websnap), })

        if BMMuser.post_webcam:
            kafka_message({'echoslack': True,
                           'img': os.path.join(proposal_base(), 'snapshots', websnap)})

        ### --- analog camera using redgo dongle ------------------------------------------
        ###     this can only be read by a client on xf06bm-ws3, so... not QS on srv1
        thishost = socket.gethostname()
        if is_re_worker_active() is False and 'ws3' in thishost:
            print(whisper('The error text below saying "Error opening file for output:"'))
            print(whisper('happens every time and does not indicate a problem of any sort.'))
            anasnap = "%s_analog_%s.jpg" % (stub, ahora)
            image_ana = os.path.join(folder, 'snapshots', anasnap)
            md['_filename'] = image_ana
            anacam._annotation_string = stub
            print(bold_msg('analog camera snapshot'))
            anauid = yield from count([anacam], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
            print(whisper('The error text above saying "Error opening file for output:"'))
            print(whisper('happens every time and does not indicate a problem of any sort.\n'))
            self.anasnap, self.anauid = anasnap, anauid
            # try:
            #     im = Image.fromarray(numpy.array(bmm_catalog[self.anauid].primary.read()['anacam_image'])[0])
            #     im.save(image_ana, 'JPEG')
            #     if BMMuser.post_anacam:
            #         kafka_message({'echoslack': True,
            #                        'img': image_ana})
            # except:
            #     print(error_msg('Could not copy analog snapshot, probably because it\'s capture failed.'))
            #     anacam_uid = False
            #     pass
            kafka_message({'copy': True,
                       'file': file_resource(anauid),
                       'target': os.path.join(proposal_base(), 'snapshots', anasnap), })
            if BMMuser.post_anacam:
                kafka_message({'echoslack': True,
                               'img': os.path.join(proposal_base(), 'snapshots', anasnap)})

            
        ### --- USB camera #1 --------------------------------------------------------------
        usb1snap = "%s_usb1_%s.jpg" % (stub, ahora)
        image_usb1 = os.path.join(folder, 'snapshots', usb1snap)
        md['_filename'] = image_usb1
        usbcam1._annotation_string = stub
        print(bold_msg('USB camera #1 snapshot'))
        usb1uid = yield from count([usbcam1], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
        self.usb1snap, self.usb1uid = usb1snap, usb1uid
        #yield from sleep(0.5)
        # im = Image.fromarray(numpy.array(bmm_catalog[self.usb1uid].primary.read()['usbcam1_image'])[0])
        # im.save(image_usb1, 'JPEG')
        kafka_message({'copy': True,
                       'file': file_resource(usb1uid),
                       'target': os.path.join(proposal_base(), 'snapshots', usb1snap), })
        if BMMuser.post_usbcam1:
            kafka_message({'echoslack': True,
                           'img': os.path.join(proposal_base(), 'snapshots', usb1snap)})

        ### --- USB camera #2 --------------------------------------------------------------
        usb2snap = "%s_usb2_%s.jpg" % (stub, ahora)
        image_usb2 = os.path.join(folder, 'snapshots', usb2snap)
        md['_filename'] = image_usb2
        usbcam2._annotation_string = stub
        print(bold_msg('USB camera #2 snapshot'))
        usb2uid = yield from count([usbcam2], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
        self.usb2snap, self.usb2uid = usb2snap, usb2uid
        #yield from sleep(0.5)
        # im = Image.fromarray(numpy.array(bmm_catalog[self.usb2uid].primary.read()['usbcam2_image'])[0])
        # im.save(image_usb2, 'JPEG')
        kafka_message({'copy': True,
                       'file': file_resource(usb2uid),
                       'target': os.path.join(proposal_base(), 'snapshots', usb2snap), })
        if BMMuser.post_usbcam2:
            kafka_message({'echoslack': True,
                           'img': os.path.join(proposal_base(), 'snapshots', usb2snap)})
       
        ### --- capture metadata for dossier -----------------------------------------------
        self.cameras_md = {'webcam_file': websnap,  'webcam_uid': webuid,
                           'analog_file': anasnap,  'anacam_uid': anauid,
                           'usb1_file':   usb1snap, 'usbcam1_uid': usb1uid,
                           'usb2_file':   usb2snap, 'usbcam2_uid': usb2uid, }
