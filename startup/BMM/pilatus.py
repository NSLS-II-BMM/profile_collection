
####################################################
# this script has not had .value changed to .get() #
####################################################

from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, AreaDetector, SingleTrigger

from ophyd.areadetector.plugins import ImagePlugin_V33, TIFFPlugin

import time, os
import numpy
#from PIL import Image
import matplotlib.pyplot  as plt
from scipy import ndimage

class MyDetector(SingleTrigger, AreaDetector):
    image         = Cpt(ImagePlugin_V33, 'image1:')
    _path         = Cpt(EpicsSignal,   'cam1:FilePath')
    _fname        = Cpt(EpicsSignal,   'cam1:FileName')
    _number       = Cpt(EpicsSignal,   'cam1:FileNumber')
    _template     = Cpt(EpicsSignal,   'cam1:FileTemplate')
    _threshold    = Cpt(EpicsSignal,   'cam1:ThresholdEnergy')
    _fullname     = Cpt(EpicsSignalRO, 'cam1:FullFileName_RBV')
    _statusmsg    = Cpt(EpicsSignalRO, 'cam1:StatusMessage_RBV')
    _busy         = Cpt(EpicsSignalRO, 'cam1:AcquireBusy')
    autoincrement = Cpt(EpicsSignal,   'cam1:AutoIncrement')
    _energy       = Cpt(EpicsSignalRO, 'cam1:Energy')
    threshold_apply = Cpt(EpicsSignalRO, 'cam1:ThresholdAutoApply')
    tiff1           = Cpt(TIFFPlugin, 'TIFF1:')

    @property
    def path(self):
        return(''.join([chr(x) for x in self._path.get()[self._path.get().nonzero()]]) )
    @path.setter
    def path(self, path):
        a = numpy.pad(numpy.array([ord(x) for x in path]), (0,256-len(path)), mode='constant')
        self._path.put(a)
        self.tiff1.file_path.put(a)

    @property
    def fname(self):
        return(''.join([chr(x) for x in self._fname.get()[self._fname.get().nonzero()]]) )
    @fname.setter
    def fname(self, fname):
        a = numpy.pad(numpy.array([ord(x) for x in fname]), (0,256-len(fname)), mode='constant')
        self._fname.put(a)
        self.tiff1.file_name.put(a)
    
    @property
    def template(self):
        return(''.join([chr(x) for x in self._template.get()[self._template.get().nonzero()]]) )
    @template.setter
    def template(self, template):
        a = numpy.pad(numpy.array([ord(x) for x in template]), (0,256-len(template)), mode='constant')
        self._template.put(a)
        self.tiff1.file_template.put(a)

    @property
    def fullname(self):
        return(''.join([chr(x) for x in self._fullname.get()[self._fullname.get().nonzero()]]) )

    @property
    def statusmsg(self):
        return(''.join([chr(x) for x in self._statusmsg.get()[self._statusmsg.get().nonzero()]]) )

    @property
    def number(self):
        return(self._number.get())
    @number.setter
    def number(self, number):
        self._number.put(number)
        self.tiff1.file_number.put(number)
    
    @property
    def threshold(self):
        return(self._threshold.get())
    @threshold.setter
    def threshold(self, threshold_value):
        self._threshold.put(threshold_value)

    @property
    def energy(self):
        return(self._energy.get())
    @energy.setter
    def energy(self, energy_value):
        self._energy.put(energy_value)

    @property
    def time(self):
        return(self.cam.acquire_time.get())
    @time.setter
    def time(self, exposure_time):
        self.cam.acquire_time.put(exposure_time)
        self.cam.acquire_period.put(exposure_time + 0.004)

    @property
    def numimages(self):
        return(self.cam.num_images.get())
    @time.setter
    def numimages(self, numimages):
        self.cam.num_images.put(numimages)

    @property
    def ready(self):
        if self._busy.get() == 1:
            return False
        elif 'Error' in self.statusmsg:
            return False
        else:
            return True


    

class PilatusGrabber():
    '''Crude tool for grabbing images from the Pilatus.  Largely following
    the standard BlueSky AreaDetector interface, but monkey-patching
    functionality for the bits that Bruce is too dim to figure out.

    Parameters
    ----------
    path : str
        AreaDetector's file path (cannot have spaces)
    fname : str
        file name
    template : str
        substitution template for constructing the resolved file name
    fullname : str
        AreaDetector's fully resolved file name
    number : int
        file extension (auto increments)
    threshold : float
        detector energy threshold in keV
    time : float
        exposure time, sets the exposure time and acquire time
    ready : bool
        flag with a simple check to see if camera is ready to take a picture

    Examples
    --------
    Define the Pilatus Detector

    >>> pilatus = MyDetector('XF:06BMB-ES{Det:PIL100k}:', name='Pilatus')

    Make an PilatusGrabber opbject
       
    >>> pil = PilatusGrabber(pilatus)

    Take an exposure
       
    >>> pil.snap()

    Show the image (and maybe copy it elsewhere)
       
    >>> pil.fetch()

    '''
    def __init__(self, source):
        self.source     = source
        self.image      = EpicsSignal(self.source.prefix + 'image1:ArrayData', name=self.source.name + ' image')
        self._path      = EpicsSignal(self.source.prefix + 'cam1:FilePath')
        self._fname     = EpicsSignal(self.source.prefix + 'cam1:FileName')
        self._number    = EpicsSignal(self.source.prefix + 'cam1:FileNumber')
        self._template  = EpicsSignal(self.source.prefix + 'cam1:FileTemplate')
        self._threshold = EpicsSignal(self.source.prefix + 'cam1:ThresholdEnergy')
        self._fullname  = EpicsSignalRO(self.source.prefix + 'cam1:FullFileName_RBV')
        self._statusmsg = EpicsSignalRO(self.source.prefix + 'cam1:StatusMessage_RBV')
        self._busy      = EpicsSignalRO(self.source.prefix + 'cam1:AcquireBusy')
        self.autoincrement = EpicsSignal(self.source.prefix + 'cam1:AutoIncrement')
        
    @property
    def path(self):
        return(''.join([chr(x) for x in self._path.value[self._path.value.nonzero()]]) )
    @path.setter
    def path(self, path):
        a = numpy.pad(numpy.array([ord(x) for x in path]), (0,256-len(path)), mode='constant')
        self._path.put(a)

    @property
    def fname(self):
        return(''.join([chr(x) for x in self._fname.value[self._fname.value.nonzero()]]) )
    @fname.setter
    def fname(self, fname):
        a = numpy.pad(numpy.array([ord(x) for x in fname]), (0,256-len(fname)), mode='constant')
        self._fname.put(a)
    
    @property
    def template(self):
        return(''.join([chr(x) for x in self._template.value[self._template.value.nonzero()]]) )
    @template.setter
    def template(self, template):
        a = numpy.pad(numpy.array([ord(x) for x in template]), (0,256-len(template)), mode='constant')
        self._template.put(a)

    @property
    def fullname(self):
        return(''.join([chr(x) for x in self._fullname.value[self._fullname.value.nonzero()]]) )

    @property
    def statusmsg(self):
        return(''.join([chr(x) for x in self._statusmsg.value[self._statusmsg.value.nonzero()]]) )

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

    @property
    def ready(self):
        if self._busy.value == 1:
            return False
        elif 'Error' in self.statusmsg:
            return False
        else:
            return True
        
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
        img = numpy.reshape(array, size).astype('float')
            
        #Image.fromarray(img).save(fname, "TIFF")
        ## symlink to file on /nist ???  copy???
        
        fig,ax = plt.subplots(1)  # Create figure and axes
        #rotated_img = ndimage.rotate(img, 90)
        plt.imshow(img, cmap='bone') ## https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
        
        imfile = os.path.basename(self.fullname)
        plt.title(imfile)
        plt.colorbar()
        plt.xlim([147,206])
        plt.ylim([77,98])
        plt.clim(0, array.max())
        plt.show()

