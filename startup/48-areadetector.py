from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, AreaDetector, SingleTrigger, ImagePlugin

import numpy as np
#from PIL import Image
import matplotlib.pyplot  as plt
from scipy import ndimage

run_report(__file__)

class MyDetector(SingleTrigger, AreaDetector):
    image = Cpt(ImagePlugin, 'image1:')
    #pass


class PilatusGrabber():
    '''Crude tool for grabbing images from the Pilatus.  Largely based on
    the standard BlueSky AreaDetector interface, but monkey patching
    functionality for the bits that I am too dim to figure out.

    Define the Pilatus Detector
       pilatus = MyDetector('XF:06BMB-ES{Det:PIL100k}:', name='Pilatus')

    Make an ImageGrabber opbject
       pil = ImageGrabber(pilatus)

    Take an exposure
       pil.snap()

    Show the image (and maybe copy it elsewhere)
       pil.fetch()

    Properties:
       path:      AreDetector's file path
       fname:     file name
       template:  substitution template for constructing the resolved file name
       fullname:  AreDetector's fully resolved file name
       number:    file extension (auto increments)
       threshold: detector energy threshold in keV
       time:      exposure time, sets the exposure time and acquire time

    '''
    def __init__(self, source):
        self.source     = source
        self.image      = EpicsSignal(self.source.prefix + 'image1:ArrayData', name=self.source.name + ' image')
        self._path      = EpicsSignal(self.source.prefix + 'cam1:FilePath')
        self._fname     = EpicsSignal(self.source.prefix + 'cam1:FileName')
        self._number    = EpicsSignal(self.source.prefix + 'cam1:FileNumber')
        self._template  = EpicsSignal(self.source.prefix + 'cam1:FileTemplate')
        self._fullname  = EpicsSignalRO(self.source.prefix + 'cam1:FullFileName_RBV')
        self._threshold = EpicsSignal(self.source.prefix + 'cam1:ThresholdEnergy')
        
    @property
    def path(self):
        return(''.join([chr(x) for x in self._path.value[self._path.value.nonzero()]]) )
    @path.setter
    def path(self, path):
        a = numpy.pad(array([ord(x) for x in path]), (0,256-len(path)), mode='constant')
        self._path.put(a)

    @property
    def fname(self):
        return(''.join([chr(x) for x in self._fname.value[self._fname.value.nonzero()]]) )
    @fname.setter
    def fname(self, fname):
        a = numpy.pad(array([ord(x) for x in fname]), (0,256-len(fname)), mode='constant')
        self._fname.put(a)
    
    @property
    def template(self):
        return(''.join([chr(x) for x in self._template.value[self._template.value.nonzero()]]) )
    @template.setter
    def template(self, template):
        a = numpy.pad(array([ord(x) for x in template]), (0,256-len(template)), mode='constant')
        self._template.put(a)

    @property
    def fullname(self):
        return(''.join([chr(x) for x in self._fullname.value[self._fullname.value.nonzero()]]) )

    @property
    def number(self):
        return(self._number.value)
    @number.setter
    def number(self, number):
        self._number.put(number)
    
    @property
    def threshold(self):
        return(self._threshold.value)
    @threshold.setter
    def threshold(self, threshold):
        self._threshold.put(threshold)

    @property
    def time(self):
        return(self.source.cam.acquire_time.value)
    @time.setter
    def time(self, exposure_time):
        self.source.cam.acquire_time.put(exposure_time)
        self.source.cam.acquire_period.put(exposure_time + 0.004)

    @property
    def numimages(self):
        return(self.source.cam.num_images.value)
    @time.setter
    def numimages(self, numimages):
        self.source.cam.num_images.put(numimages)
        
        
    def snap(self):
        self.source.stage()
        st = self.source.trigger()
        while not st.done:
            time.sleep(.1)
        ret = self.source.read()
        desc = self.source.describe()
        self.source.unstage()

    
    def fetch(self, fname='/home/xf06bm/test.tif'):
        array = self.image.get()
        size  = (self.source.image.height.value, self.source.image.width.value)
        img = np.reshape(array, size).astype('float')
            
        #Image.fromarray(img).save(fname, "TIFF")
        ## symlink to file on /nist ???  copy???
        
        fig,ax = plt.subplots(1)  # Create figure and axes
        rotated_img = ndimage.rotate(img, 90)
        plt.imshow(rotated_img, cmap='bone') ## https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html

        imfile = os.path.basename(self.fullname)
        plt.title(imfile)
        plt.colorbar()
        plt.clim(0, array.max())
        plt.show()

        
## prosilica3 = MyDetector('XF:06BM-BI{Scr:3}', name='Prosilica3')
## p3         = ImageGrabber(prosilica3)
pilatus = MyDetector('XF:06BMB-ES{Det:PIL100k}:', name='Pilatus')
pil     = PilatusGrabber(pilatus)
