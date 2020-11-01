import os
import uuid
import threading
import itertools
import numpy

import requests
import bluesky
from ophyd import Device, Component, Signal, DeviceStatus
from ophyd.areadetector.filestore_mixins import resource_factory

# See for resource_factory docstring
# https://github.com/bluesky/ophyd/blob/b1d258a36c974013b6e3ac8ee7112ed876b7653a/ophyd/areadetector/filestore_mixins.py#L70-L112

import requests
from PIL import Image, ImageFont, ImageDraw 
from io import BytesIO

from os import system
from subprocess import Popen, PIPE, call
import fcntl

try:
    from bluesky_queueserver.manager.profile_tools import set_user_ns
except ModuleNotFoundError:
    from ._set_user_ns import set_user_ns

## from IPython import get_ipython
## user_ns = get_ipython().user_ns

from BMM.db import file_resource
from BMM.functions import now
from BMM.logging import report


def annotate_image(imagefile, text):
    bluesky_path_as_list = bluesky.__path__[0].split('/') # crude, but finds current collection folder
    font_path = os.path.join('/', *bluesky_path_as_list[:4], 'lib', 'python3.7', 'site-packages', 'matplotlib', 'mpl-data', 'fonts', 'ttf')
    img = Image.open(imagefile)
    width, height = img.size
    draw = ImageDraw.Draw(img, 'RGBA')
    draw.rectangle(((0, int(9.5*height/10)), (width, height)), fill=(255,255,255,125))
    font = ImageFont.truetype(font_path + '/DejaVuSans.ttf', 24)
    draw.text((int(0.2*width/10), int(9.6*height/10)), text, (0,0,0), font=font)
    img.save(imagefile)

def xas_webcam(filename=None, **kwargs):
    XASURL = 'http://xf06bm-cam6/axis-cgi/jpg/image.cgi'
    CAM_PROXIES = {"http": None, "https": None,}
    if filename is None:
        filename = os.environ['HOME'] + '/XAS_camera_' + now() + '.jpg'
    r=requests.get(XASURL, proxies=CAM_PROXIES)
    Image.open(BytesIO(r.content)).save(filename, 'JPEG')
    if 'annotation' in kwargs:
        annotate_image(filename, kwargs['annotation'])
    report('XAS webcam image written to %s' % filename)

def xrd_webcam(filename=None, **kwargs):
    XRDURL = 'http://xf06bm-cam6/axis-cgi/jpg/image.cgi'
    CAM_PROXIES = {"http": None, "https": None,}
    if filename is None:
        filename = os.environ['HOME'] + '/XRD_camera_' + now() + '.jpg'
    r=requests.get(XRDURL, proxies=CAM_PROXIES)
    Image.open(BytesIO(r.content)).save(filename, 'JPEG')
    if 'annotation' in kwargs:
        annotate_image(filename, kwargs['annotation'])
    report('XRD webcam image written to %s' % filename)



def analog_camera(filename    = None,
           sample      = None,
           folder      = os.environ['HOME'],
           device      = '/dev/video0',
           camera      = 0,
           skip        = 30,
           frames      = 5,
           brightness  = 20,
           x           = 320,
           y           = 240,
           linecolor   = 'white',
           nocrosshair = True,
           quiet       = False,
           reset       = False,
           usbid       = '534d:0021',
           title       = 'NIST BMM (NSLS-II 06BM)',
           timestamp   = '%Y-%m-%d %H:%M:%S'):

    """A function for interacting with fswebcam in a way that meets the
    needs of 06BM.

    Parameters
    ----------
    folder : str
        location to drop jpg image [$HOME]
    device : str
        char device of camera [/dev/video0]
    camera : int
        camera number[0]
    skip : int
        number of frames to skip waiting for camera to wake up  [30]
    frames : int
        number of frames to accumulate in image [5]
    brightness : int
        brightness setting of camera as a percentage [20]
    x : int
        middle of image, in pixels,  X-location of cross hair [320]
    y : int
        middle of image, in pixels,  Y-location of cross hair [240]
    linecolor : str
        color of cross hair lines [white]
    nocrosshair : bool
        flag to suppress cross hair [True]
    quiet : bool
        flag to suppress screen messages [False]
    usbid : str
        vendor and product ID of camera of AV to USB device at 06BM [534d:0021]
    title : str
        title string for fswebcam banner [NIST BMM (NSLS-II 06BM)]
    filename : str
        output file name                   

    """

    USBDEVFS_RESET= 21780

    if reset is True:
        if not quiet: print("resetting video device")
        try:
            lsusb_out = Popen("lsusb | grep -i %s" % usbid,
                              shell=True,
                              bufsize=64,
                              stdin=PIPE,
                              stdout=PIPE, close_fds=True).stdout.read().strip().split()
            bus = lsusb_out[1].decode('UTF-8')
            device = lsusb_out[3][:-1].decode('UTF-8')
            print("/dev/bus/usb/%s/%s"%(bus, device))
            f = open("/dev/bus/usb/%s/%s"%(bus, device), 'w', os.O_WRONLY)
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
            sleep(1)
        except Exception as msg:
            print("failed to reset device:", msg)

    quiet = ''
    if quiet: quiet = '-q '
    if filename is None:
        filename = folder + '/analog_camera_' + now() + '.jpg'

    if sample is not None:
        title = title + ' - ' + sample
    command = "fswebcam %s-i %s -d %s -r 640x480 --title \"%s\" --timestamp \"%s\" -S %d -F %d --set brightness=%s%% \"%s\"" %\
              (quiet, camera, device, title, timestamp, skip, frames, brightness, filename)
    system(command)

    report('Analog camera image written to %s' % filename)

    ## crosshairs
    #if not camera.nocrosshair:
    #    camera.crosshairs()




class BMM_JPEG_HANDLER:
    def __init__(self, resource_path):
        # resource_path is really a template string with a %d in it
        self._template = resource_path

    def __call__(self, index):
        filepath = self._template % index
        return numpy.asarray(Image.open(filepath))


@set_user_ns
def set_db(user_ns):
    db = user_ns['db']
    db.reg.register_handler("BMM_XAS_WEBCAM",    BMM_JPEG_HANDLER)
    db.reg.register_handler("BMM_XRD_WEBCAM",    BMM_JPEG_HANDLER)
    db.reg.register_handler("BMM_ANALOG_CAMERA", BMM_JPEG_HANDLER)


set_db()


class ExternalFileReference(Signal):
    """
    A pure software signal where a Device can stash a datum_id
    """
    def __init__(self, *args, shape, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape = shape

    def describe(self):
        res = super().describe()
        res[self.name].update(dict(external="FILESTORE:", dtype="array", shape=self.shape))
        return res


class BMMSnapshot(Device):
    image = Component(ExternalFileReference, value="", kind="normal", shape=[])

    def __init__(self, *args, root, which, **kwargs):
        super().__init__(*args, **kwargs)
        self._root = root
        self._acquiring_lock = threading.Lock()
        self._counter = None  # set to an itertools.count object when staged
        self._asset_docs_cache = []
        self._annotation_string = ''
        if which.lower() =='xrd':
            self._SPEC = "BMM_XRD_WEBCAM"
            self._url = 'http://xf06bm-cam5/axis-cgi/jpg/image.cgi'
        elif which.lower() == 'xas':
            self._SPEC = "BMM_XAS_WEBCAM"
            self._url = 'http://xf06bm-cam6/axis-cgi/jpg/image.cgi'
        else:
            self._SPEC = "BMM_ANALOG_CAMERA"
            self._url = None

    def stage(self):
        #self._rel_path_template = f"path/to/files/{uuid.uuid4()}_%d.ext"
        self._rel_path_template = f"{uuid.uuid4()}_%d.jpg"
        resource, self._datum_factory = resource_factory(
            self._SPEC, self._root, self._rel_path_template, {}, "posix")
        self._asset_docs_cache.append(('resource', resource))
        self._counter = itertools.count()
        # Set the filepath
        return super().stage()

    def collect_asset_docs(self):
        yield from self._asset_docs_cache
        self._asset_docs_cache.clear()

    def unstage(self):
        self._counter = None
        self._asset_docs_cache.clear()
        return super().unstage()

    def _capture(self, status, i):
        "This runs on a background thread."
        try:
            if not self._acquiring_lock.acquire(timeout=0):
                raise RuntimeError("Cannot trigger, currently trigggering!")
            filename = os.path.join(self._root, self._rel_path_template % i)
            # Kick off requests, or subprocess, or whatever with the result
            # that a file is saved at `filename`.

            if self._SPEC == "BMM_XAS_WEBCAM" or self._SPEC == "BMM_XRD_WEBCAM":
                CAM_PROXIES = {"http": None, "https": None,}
                r=requests.get(self._url, proxies=CAM_PROXIES)
                im = Image.open(BytesIO(r.content))
                im.save(filename, 'JPEG')
                #print(f'w: {im.width}    h: {im.height}')
                self.image.shape = (im.height, im.width, 3)

                annotation = 'NIST BMM (NSLS-II 06BM)      ' + self._annotation_string + '      ' + now()
                annotate_image(filename, annotation)
            else:
                analog_camera(filename=filename, sample=self._annotation_string, folder=self._root, quiet=True)
                self.image.shape = (480, 640, 3)
            self._annotation_string = ''

            datum = self._datum_factory({"index": i})
            self._asset_docs_cache.append(('datum', datum))
            self.image.set(datum["datum_id"]).wait()
        except Exception as exc:
            status.set_exception(exc)
        else:
            status.set_finished()
        finally:
            self._acquiring_lock.release()

    def trigger(self):
        status = DeviceStatus(self)
        i = next(self._counter)
        thread = threading.Thread(target=self._capture, args=(status, i))
        thread.start()
        return status

def snap(which, filename=None, **kwargs):
    if which is None: which = 'XAS'
    if which.lower() == 'xrd':
        xrd_webcam(filename=filename, **kwargs)
    elif 'ana' in which.lower() :
        analog_camera(filename=filename, **kwargs)
    else:
        xas_webcam(filename=filename, **kwargs)



