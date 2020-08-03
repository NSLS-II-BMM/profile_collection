
from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.sim import NullStatus  # TODO: remove after complete/collect are defined
from ophyd import Component as Cpt, set_and_wait

from pathlib import PurePath
#from hxntools.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
#                                         Xspress3Channel, Xspress3FileStore, logger)
from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
                                       Xspress3Channel, Xspress3FileStore, logger)

import numpy
import itertools
import time as ttime
from collections import deque, OrderedDict

import matplotlib.pyplot as plt
from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper


class Xspress3FileStoreFlyable(Xspress3FileStore):
    def warmup(self):
        """
        A convenience method for 'priming' the plugin.
        The plugin has to 'see' one acquisition before it is ready to capture.
        This sets the array size, etc.
        NOTE : this comes from:
            https://github.com/NSLS-II/ophyd/blob/master/ophyd/areadetector/plugins.py
        We had to replace "cam" with "settings" here.
        Also modified the stage sigs.
        """
        print("warming up the hdf5 plugin...")
        set_and_wait(self.enable, 1)
        sigs = OrderedDict([(self.parent.settings.array_callbacks, 1),
                            (self.parent.settings.trigger_mode, 'Internal'),
                            # just in case the acquisition time is set very long...
                            (self.parent.settings.acquire_time, 1),
                            # (self.capture, 1),
                            (self.parent.settings.acquire, 1)])

        original_vals = {sig: sig.get() for sig in sigs}

        # Remove the hdf5.capture item here to avoid an error as it should reset back to 0 itself
        # del original_vals[self.capture]

        for sig, val in sigs.items():
            ttime.sleep(0.1)  # abundance of caution
            set_and_wait(sig, val)

        ttime.sleep(2)  # wait for acquisition

        for sig, val in reversed(list(original_vals.items())):
            ttime.sleep(0.1)
            set_and_wait(sig, val)
        print("done")

    def unstage(self):
        """A custom unstage method is needed to avoid these messages:

        Still capturing data .... waiting.
        Still capturing data .... waiting.
        Still capturing data .... waiting.
        Still capturing data .... giving up.
        """
        set_and_wait(self.capture, 0)
        return super().unstage()


class BMMXspress3Detector(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    channel2 = Cpt(Xspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    channel3 = Cpt(Xspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    channel4 = Cpt(Xspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    #create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    # mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')
    # mca2_sum = Cpt(EpicsSignal, 'ARRSUM2:ArrayData')
    # mca3_sum = Cpt(EpicsSignal, 'ARRSUM3:ArrayData')
    # mca4_sum = Cpt(EpicsSignal, 'ARRSUM4:ArrayData')
    
    mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')
    mca2 = Cpt(EpicsSignal, 'ARR2:ArrayData')
    mca3 = Cpt(EpicsSignal, 'ARR3:ArrayData')
    mca4 = Cpt(EpicsSignal, 'ARR4:ArrayData')
    
    hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF5:',
               read_path_template='/home/xspress3/data/BMM',
               root='/home/xspress3',
               write_path_template='/home/xspress3/data/BMM',
               )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.settings.num_images.put(1)   # number of frames
        self.settings.trigger_mode.put(1) # trigger mode internal
        self.settings.ctrl_dtc.put(1)     # dead time corrections enabled
        self.set_channels_for_hdf5()
        self.slots = [None,]*16
        self.set_rois()

    def restart(self):
        for n in range(1,5):
            this = getattr(self, f'channel{n}')
            this.vis_enabled.put(1)
        self.settings.num_images.put(1)   # number of frames
        self.settings.trigger_mode.put(1) # trigger mode internal
        self.settings.ctrl_dtc.put(1)     # dead time corrections enabled
        self.set_channels_for_hdf5()
        self.set_rois()
        
    def _acquire_changed(self, value=None, old_value=None, **kwargs):
        super()._acquire_changed(value=value, old_value=old_value, **kwargs)
        status = self._status
        if status is not None and status.done:
            # Clear the state to be ready for the next round.
            self._status = None
            
    def stop(self):
        ret = super().stop()
        self.hdf5.stop()
        return ret

    def stage(self):
        if self.spectra_per_point.get() != 1:
            raise NotImplementedError(
                "multi spectra per point not supported yet")
        ret = super().stage()
        return ret

    def unstage(self):
        self.settings.trigger_mode.put(0)  # 'Software'
        super().unstage()

    def set_channels_for_hdf5(self, channels=(1, 2, 3, 4)):
        """
        Configure which channels' data should be saved in the resulted hdf5 file.

        Parameters
        ----------
        channels: tuple, optional
            the channels to save the data for
        """
        # The number of channel
        for n in channels:
            getattr(self, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
        self.hdf5.num_extra_dims.put(0)
        self.settings.num_channels.put(len(channels))

    # Currently only using four channels. Uncomment these to enable more
    # channels:
    # channel5 = C(Xspress3Channel, 'C5_', channel_num=5)
    # channel6 = C(Xspress3Channel, 'C6_', channel_num=6)
    # channel7 = C(Xspress3Channel, 'C7_', channel_num=7)
    # channel8 = C(Xspress3Channel, 'C8_', channel_num=8)

    def set_roi_channel(self, channel=1, index=4, name='OCR', low=1, high=4095):
        ch = getattr(self, f'channel{channel}')
        rs = ch.rois
        this = getattr(rs, 'roi{:02}'.format(index))
        this.value.name = name
        this.bin_low.put(low)
        this.bin_high.put(high)
        
    def set_rois(self):
        self.slots[0:3] = ['Ti', 'Mn', 'Fe', 'OCR']
        for n in range(1,5):
            self.set_roi_channel(channel=n, index=1, name=f'Ti{n}',  low=440, high=459)
            self.set_roi_channel(channel=n, index=2, name=f'Mn{n}',  low=580, high=598)
            self.set_roi_channel(channel=n, index=3, name=f'Fe{n}',  low=626, high=651)
            self.set_roi_channel(channel=n, index=4, name=f'OCR{n}', low=1,   high=4095)

    def measure_roi(self):
        BMMuser = user_ns['BMMuser']
        for i in range(4):
            for n in range(1,5):
                ch = getattr(self, f'channel{n}')
                this = getattr(ch.rois, 'roi{:02}'.format(i+1))
                if self.slots[i] == BMMuser.element:
                    this.value.kind = 'hinted'
                    setattr(BMMuser, f'xs{n}', this.value.name)
                    setattr(BMMuser, f'xschannel{n}', this.value)
                else:
                    this.value.kind = 'omitted'
                

    def show_rois(self):
        BMMuser = user_ns['BMMuser']
        text = 'Xspress3 ROIs:\n'
        text += bold_msg('    1      2      3      4      5      6      7      8\n')
        text += ' '
        for i in range(8):
            if self.slots[i] == BMMuser.element:
                text += go_msg('%4.4s' % self.slots[i]) + '   '
            else:
                text += '%4.4s' % self.slots[i] + '   '
        text += '\n'
        text += bold_msg('    9     10     11     12     13     14     15     16\n')
        text += ' '
        for i in range(8, 16):
            if self.slots[i] == BMMuser.element:
                text += go_msg('%4.4s' % self.slots[i]) + '   '
            else:
                text += '%4.4s' % self.slots[i] + '   '
        text += '\n'
        return(text)
            
    def plot(self, add=False, only=None):
        dcm = user_ns['dcm']
        plt.cla()
        plt.xlabel('Energy  (eV)')
        plt.ylabel('counts')
        plt.title('XRF Spectrum')
        plt.grid(which='major', axis='both')
        plt.xlim(2500, round(dcm.energy.position, -2)+500)
        e = numpy.arange(0, len(self.mca1.value)) * 10
        if only is not None:
            this = getattr(self, f'mca{only}')
            plt.plot(e, this.value)
        elif add is True:
            plt.plot(e, self.mca1.value+self.mca2.value+self.mca3.value+self.mca4.value)
        else:
            plt.plot(e, self.mca1.value)
            plt.plot(e, self.mca2.value)
            plt.plot(e, self.mca3.value)
            plt.plot(e, self.mca4.value)
        
