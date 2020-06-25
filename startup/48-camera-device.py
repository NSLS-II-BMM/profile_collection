import os
import uuid
import threading
import itertools

import requests
from ophyd import Device, Component, Signal, DeviceStatus
from ophyd.areadetector.filestore_mixins import resource_factory

# See for resource_factory docstring
# https://github.com/bluesky/ophyd/blob/b1d258a36c974013b6e3ac8ee7112ed876b7653a/ophyd/areadetector/filestore_mixins.py#L70-L112

import requests
from PIL import Image, ImageFont, ImageDraw 
from io import BytesIO

run_report(__file__, text='Web and analog cameras as Ophyd devices')

class BMM_JPEG_HANDLER:
    def __init__(self, resource_path):
        # resource_path is really a template string with a %d in it
        self._template = resource_path

    def __call__(self, index):
        filepath = self._template % index
        return np.asarray(Image.open(filepath))

db.reg.register_handler("BMM_XAS_WEBCAM",    BMM_JPEG_HANDLER)
db.reg.register_handler("BMM_XRD_WEBCAM",    BMM_JPEG_HANDLER)
db.reg.register_handler("BMM_ANALOG_CAMERA", BMM_JPEG_HANDLER)

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


class AxisWebCamera(Device):
    image = Component(ExternalFileReference, value="", kind="normal", shape=[])

    def __init__(self, *args, root, which, **kwargs):
        super().__init__(*args, **kwargs)
        self._root = root
        self._acquiring_lock = threading.Lock()
        self._counter = None  # set to an itertools.count object when staged
        self._asset_docs_cache = []
        if which =='XRD':
            self._SPEC = "BMM_XRD_WEBCAM"
            self._url = 'http://10.6.129.55/axis-cgi/jpg/image.cgi'
        else:
            self._SPEC = "BMM_XAS_WEBCAM"
            self._url = 'http://10.6.129.56/axis-cgi/jpg/image.cgi'

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

            #XASURL = 'http://10.6.129.56/axis-cgi/jpg/image.cgi'
            #XRDURL = 'http://10.6.129.55/axis-cgi/jpg/image.cgi'
            CAM_PROXIES = {"http": None, "https": None,}
            r=requests.get(self._url, proxies=CAM_PROXIES)
            im = Image.open(BytesIO(r.content))
            im.save(filename, 'JPEG')
            #print(f'w: {im.width}    h: {im.height}')
            self.image.shape = (im.height, im.width, 3)
            
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


xascam = AxisWebCamera(root='/nist/xf06bm/experiments/XAS/snapshots', which='XAS', name='xascam')
xrdcam = AxisWebCamera(root='/nist/xf06bm/experiments/XAS/snapshots', which='XRD', name='xrdcam')
