
from ophyd import (SingleTrigger, AreaDetector, DetectorBase, Component as Cpt, Device,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)

from ophyd.areadetector.plugins import ImagePlugin_V33, TIFFPlugin

import time
from PIL import Image, ImageFont, ImageDraw 
import numpy as np
from BMM.camera_device import annotate_image
from BMM.functions import now
import sys, datetime, uuid, itertools

from ophyd.areadetector.base import NDDerivedSignal
from ophyd.areadetector.filestore_mixins import resource_factory

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)
md = user_ns["RE"].md


class MyHack(NDDerivedSignal):
    
    def inverse(self, value):
        """Shape the flat array to send as a result of ``.get``"""
        array_shape = self.derived_shape[:self.derived_ndims]
        if not any(array_shape):
            raise RuntimeError(f"Invalid array size {self.derived_shape}")

        array_len = np.prod(array_shape)
        if len(value) < array_len:
            raise RuntimeError(f"cannot reshape array of size {len(value)} "
                               f"into shape {tuple(array_shape)}. Check IOC configuration.")

        return np.array(value[:array_len]).reshape(array_shape)

class MyImage(ImagePlugin_V33):
    shaped_image = Cpt(MyHack, derived_from='array_data',
                       shape=('array_size.depth',
                              'array_size.height',
                              'array_size.width'),
                       num_dimensions='ndimensions',
                       kind='omitted', lazy=True)

class ParsimoniousImage(ImagePlugin_V33):
    shaped_image = None 

class CAMERA(SingleTrigger, AreaDetector):
    # image = Cpt(ImagePlugin_V33, 'image1:')
    image = Cpt(ParsimoniousImage, 'image1:')    
    #tiff1 = Cpt(TIFFPlugin, 'TIFF1:')
    jpeg_filepath = Cpt(EpicsSignal, 'JPEG1:FilePath')
    jpeg_filetemplate = Cpt(EpicsSignal, 'JPEG1:FileTemplate')
    jpeg_filename = Cpt(EpicsSignal, 'JPEG1:FileName')
    jpeg_autoincrement = Cpt(EpicsSignal, 'JPEG1:AutoIncrement')
    jpeg_fileformat = Cpt(EpicsSignal, 'JPEG1:FileTemplate')
    jpeg_writefile = Cpt(EpicsSignal, 'JPEG1:WriteFile')
    jpeg_create_dir_depth = Cpt(EpicsSignal, 'JPEG1:CreateDirectory')
    jpeg_autosave = Cpt(EpicsSignal, 'JPEG1:AutoSave')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._SPEC = "BMM_USBCAM"
        self._asset_docs_cache = []
    
    def _update_paths(self):
        self.jpeg_filepath.put(f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/{self.name}/{datetime.datetime.now().strftime('%Y/%m/%d')}")


    def collect_asset_docs(self):
        """The method to collect resource/datum documents."""
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        yield from items

    def stage(self, *args, **kwargs):
        self._update_paths()
        self.jpeg_filename.put(str(uuid.uuid4()))
        # self._rel_path_template = f"{self.jpeg_filename.get()}_%d.jpg"
        # self._root = self.jpeg_filepath.get()
        # resource, self._datum_factory = resource_factory(
        #     self._SPEC, self._root, self._rel_path_template, {}, "posix")
        # self._asset_docs_cache.append(('resource', resource))
        self._counter = itertools.count()
        
        super().stage(*args, **kwargs)
        # # Clear asset docs cache which may have some documents from the previous failed run.
        # self._asset_docs_cache.clear()

        # self._resource_document, self._datum_factory, _ = compose_resource(
        #     start={"uid": "needed for compose_resource() but will be discarded"},
        #     spec="BMM_JPEG_HANDLER",
        #     root=self._root_dir,
        #     resource_path=str(Path(assets_dir) / Path(data_file_with_ext)),
        #     resource_kwargs={},
        # )


        
    
    def snap(self, filename, annotation_string=''):
        if self.cam.detector_state.get() == 0:
            self.cam.acquire.put(1)
            time.sleep(0.5)
        u=self.image.array_data.get().reshape((1080,1920,3))
        im = Image.fromarray(u)
        im.save(filename, 'JPEG')
        self.image.shape = (im.height, im.width, 3)
        annotation = f'NIST BMM (NSLS-II 06BM)      camera {self.name}      {annotation_string}      {now()}'
        annotate_image(filename, annotation)
        

    
