
from ophyd import (SingleTrigger, AreaDetector, DetectorBase, Component as Cpt, Device,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)

from ophyd.areadetector.plugins import ImagePlugin_V33, TIFFPlugin

import time
from PIL import Image, ImageFont, ImageDraw 

from BMM.camera_device import annotate_image
from BMM.functions import now

class CAMERA(SingleTrigger, AreaDetector):
    image = Cpt(ImagePlugin_V33, 'image1:')
    #tiff1 = Cpt(TIFFPlugin, 'TIFF1:')

    def snap(self, filename, annotation_string=''):
        if self.cam.detector_state.get() == 0:
            self.cam.acquire.put(1)
            time.sleep(0.5)
        u=self.image.shaped_image.get()
        im = Image.fromarray(u)
        im.save(filename, 'JPEG')
        self.image.shape = (im.height, im.width, 3)
        annotation = f'NIST BMM (NSLS-II 06BM)      camera {self.name}      {annotation_string}      {now()}'
        annotate_image(filename, annotation)
        
