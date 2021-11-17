import os, uuid, threading, itertools, datetime, time
import numpy

import bluesky
from ophyd import Device, Component, Signal, DeviceStatus
from ophyd.areadetector.filestore_mixins import resource_factory

# See for resource_factory docstring
# https://github.com/bluesky/ophyd/blob/b1d258a36c974013b6e3ac8ee7112ed876b7653a/ophyd/areadetector/filestore_mixins.py#L70-L112

import requests
from PIL import Image, ImageFont, ImageDraw 
from io import BytesIO



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


class CameraSnapshot(Device):
    image = Component(ExternalFileReference, value="", kind="normal", shape=[])
    beamline_id = ''
    annotation_string = ''
    
    
    def __init__(self, *args, base, url, **kwargs):
        super().__init__(*args, **kwargs)
        self._base = base
        self._root = os.path.join(self._base, *self.today().split('-'))
        self._acquiring_lock = threading.Lock()
        self._counter = None  # set to an itertools.count object when staged
        self._asset_docs_cache = []
        self._url = url

    def current_folder(self):
        folder = os.path.join(self._base, *self.today().split('-'))
        if not os.path.isdir(folder):
            os.makedirs(folder)
        return folder
            
    def stage(self):
        self._rel_path_template = f"{uuid.uuid4()}_%d.jpg"
        self._root = self.current_folder()
        resource, self._datum_factory = resource_factory(
            "BEAMLINE_WEBCAM", self._root, self._rel_path_template, {}, "posix")
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
                raise RuntimeError("Cannot trigger, currently triggering!")
            filename = os.path.join(self._root, self._rel_path_template % i)
            # Kick off requests, or subprocess, or whatever with the result
            # that a file is saved at `filename`.

            CAM_PROXIES = {"http": None, "https": None,}
            r=requests.get(self._url, proxies=CAM_PROXIES)
            im = Image.open(BytesIO(r.content))
            im.save(filename, 'JPEG')
            #print(f'w: {im.width}    h: {im.height}')
            self.image.shape = (im.height, im.width, 3)

            annotation = f'{self.beamline_id}      {self.annotation_string}       {self.now()}'
            self.annotate_image(filename, annotation)

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

    def now(self, fmt="%Y-%m-%dT%H-%M-%S"):
        return datetime.datetime.now().strftime(fmt)
    def today(self, fmt="%Y-%m-%d-%H"):
        return datetime.datetime.today().strftime(fmt)

    def annotate_image(self, imagefile, text):
        bluesky_path_as_list = bluesky.__path__[0].split('/') # crude, but finds current collection folder
        font_path = os.path.join('/', *bluesky_path_as_list[:4], 'lib', 'python3.7', 'site-packages', 'matplotlib', 'mpl-data', 'fonts', 'ttf')
        img = Image.open(imagefile)
        width, height = img.size
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle(((0, int(9.5*height/10)), (width, height)), fill=(255,255,255,125))
        font = ImageFont.truetype(font_path + '/DejaVuSans.ttf', 24)
        draw.text((int(0.2*width/10), int(9.6*height/10)), text, (0,0,0), font=font)
        img.save(imagefile)

        
class AxisWebcam(CameraSnapshot):
    def __init__(self, *args, base, address, **kwargs):
        super().__init__(*args, base=base, url=f'http://{address}/axis-cgi/jpg/image.cgi', **kwargs)
