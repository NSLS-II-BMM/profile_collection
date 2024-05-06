
from ophyd import (SingleTrigger, AreaDetector, DetectorBase, Component as Cpt, Device,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)

from ophyd.areadetector.plugins import ImagePlugin_V33, TIFFPlugin

import time
from PIL import Image, ImageFont, ImageDraw 
import numpy as np
from BMM.camera_device import annotate_image
from BMM.functions import now
import sys

from ophyd.areadetector.base import NDDerivedSignal

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
    jpeg_filename = Cpt(EpicsSignal, 'JPEG1:FileName')
    jpeg_autoincrement = Cpt(EpicsSignal, 'JPEG1:AutoIncrement')
    jpeg_fileformat = Cpt(EpicsSignal, 'JPEG1:FileTemplate')
    jpeg_writefile = Cpt(EpicsSignal, 'JPEG1:WriteFile')
    
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
        

    
