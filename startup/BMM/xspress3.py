
from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.device import BlueskyInterface, Staged
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO, DynamicDeviceComponent as DDCpt
from ophyd.status import SubscriptionStatus, DeviceStatus
from ophyd.sim import NullStatus  # TODO: remove after complete/collect are defined
from ophyd import Component as Cpt, set_and_wait
from bluesky import __version__ as bluesky_version
from bluesky.plans import count
from bluesky.plan_stubs import abs_set, sleep, mv, null

from pathlib import PurePath
#from hxntools.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
#                                         Xspress3Channel, Xspress3FileStore, logger)
from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
                                       Xspress3Channel, Xspress3FileStore, logger)

import numpy, h5py
import pandas as pd
import itertools, os
import time as ttime
from collections import deque, OrderedDict
from itertools import product

import matplotlib.pyplot as plt
from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.db            import file_resource
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import now
from BMM.metadata      import mirror_state

from BMM.periodictable import Z_number
import json
#import configparser
        
from databroker.assets.handlers import HandlerBase, Xspress3HDF5Handler, XS3_XRF_DATA_KEY
#db = user_ns['db']
#db.reg.register_handler("BMM_XAS_WEBCAM",    Xspress3HDF5Handler)



################################################################################
# Notes:
#
# Before every count or scan, must explicitly set the number of points in the
# measurement:
#   xs.total_points.put(5) 
#
# This means that Xspress3 will require its own count plan
# also that a linescan or xafs scan must set total_points up front



# class BMMXspress3HDF5Handler(Xspress3HDF5Handler):
#     def __call__(self, *args, frame=None, **kwargs):
#         self._get_dataset()
#         shape = self.dataset.shape
#         if len(shape) != 3:
#             raise RuntimeError(f'The ndim of the dataset is not 3, but {len(shape)}')
#         num_channels = shape[1]
#         print(num_channels)
#         chanrois = [f'CHAN{c}ROI{r}' for c, r in product([1, 2, 3, 4], [1, 2, 3, 4])]
#         attrsdf = pd.DataFrame.from_dict(
#             {chanroi: self._file['/entry/instrument/detector/']['NDAttributes'][chanroi] for chanroi in chanrois}
#         )
#         ##print(attrsdf)
#         df = pd.DataFrame(data=self._dataset[frame, :, :].T,
#                           columns=[f'ch_{n+1}' for n in range(num_channels)])
#         #return pd.concat([df]+[attrsdf])
#         return df

# db = user_ns['db']
# db.reg.register_handler(BMMXspress3HDF5Handler.HANDLER_NAME,
#                         BMMXspress3HDF5Handler, overwrite=True)    

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

################################################################################
## see an example of using DynamicDeviceComponent at
## https://github.com/bluesky/ophyd/blob/70315c21903b162d6d16e6521ebac348830e59c6/ophyd/quadem.py#L80-L86
## This is a modification of the _current_fields function appropriate to this problem
def _reset_fields(attr_base, field_base, range_, **kwargs):
    defn = OrderedDict()
    for i in range_:
        attr = '{attr}{i}'.format(attr=attr_base, i=i)
        suffix = 'ROI{i}:{field}'.format(field=field_base, i=i)
        defn[attr] = (EpicsSignal, suffix, kwargs)
    return defn
    
class BMMXspress3Channel(Xspress3Channel):
    extra_rois_enabled = Cpt(EpicsSignal, 'PluginControlValExtraROI')
    resets = DDCpt(_reset_fields('reset', 'Reset', range(1, 17)))
    # reset1  = Cpt(EpicsSignal, 'ROI1:Reset')  # set this for 1 to 16, replaced by DDCpt line :)
    def reset(self):
        for r in self.resets.read_attrs:
            getattr(self.resets, r).put(1)
################################################################################
    
    
class BMMXspress3DetectorBase(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')

    channel1 = Cpt(BMMXspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    channel2 = Cpt(BMMXspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    channel3 = Cpt(BMMXspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    channel4 = Cpt(BMMXspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    channel8 = Cpt(BMMXspress3Channel, 'C8_', channel_num=8, read_attrs=['rois'])
    #create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')
    mca2_sum = Cpt(EpicsSignal, 'ARRSUM2:ArrayData')
    mca3_sum = Cpt(EpicsSignal, 'ARRSUM3:ArrayData')
    mca4_sum = Cpt(EpicsSignal, 'ARRSUM4:ArrayData')
    mca8_sum = Cpt(EpicsSignal, 'ARRSUM8:ArrayData')
    
    mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')
    mca2 = Cpt(EpicsSignal, 'ARR2:ArrayData')
    mca3 = Cpt(EpicsSignal, 'ARR3:ArrayData')
    mca4 = Cpt(EpicsSignal, 'ARR4:ArrayData')
    mca8 = Cpt(EpicsSignal, 'ARR8:ArrayData')
    
    hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF5:',
               read_path_template='/mnt/nfs/xspress3/BMM/',   # path to data folder, as mounted on client (i.e. ws1) 
               root='/mnt/nfs/xspress3/',                     # path to root, as mounted on client (i.e. ws1)
               write_path_template='/home/xspress3/data/BMM', # full path on IOC server (i.e. xf06bm-ioc-xspress3)
               )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'channel8', 'hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)

        self.set_channels_for_hdf5()

        self._asset_docs_cache = deque()
        self._datum_counter = None
        
        self.slots = ['Ti', 'V',  'Cr', 'Mn',
                      'Fe', 'Co', 'Ni', 'Cu',
                      'Zn', 'As', 'Pt', 'Pb',
                      'Ce', None, None, 'OCR']
        self.restart()
        # self.settings.num_images.put(1)   # number of frames
        # self.settings.trigger_mode.put(1) # trigger mode internal
        # self.settings.ctrl_dtc.put(1)     # dead time corrections enabled
        # self.set_channels_for_hdf5()
        # self.set_rois()

    def trigger(self):
        if self._staged != Staged.yes:
            raise RuntimeError("not staged")

        import epics
        #t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
        #print('tr1 {} '.format(t))
        self._status = DeviceStatus(self)
        #self.settings.erase.put(1)    # this was 
        self._acquisition_signal.put(1, wait=False)
        trigger_time = ttime.time()
        #t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
        #print('tr2 {} '.format(t))

        for sn in self.read_attrs:
            if sn.startswith('channel') and '.' not in sn:
                ch = getattr(self, sn)
                self.dispatch(ch.name, trigger_time)
        #t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
        #print('tr3 {} '.format(t))

        self._abs_trigger_count += 1
        return self._status
        
    def restart(self):
        for n in range(1,5):
            this = getattr(self, f'channel{n}')
            this.vis_enabled.put(1)
            this.extra_rois_enabled.put(1)
        self.channel8.vis_enabled.put(1)
        self.channel8.extra_rois_enabled.put(1)
        #XF:06BM-ES{Xsp:1}:C1_PluginControlValExtraROI
        self.settings.num_images.put(1)   # number of frames
        self.settings.trigger_mode.put(1) # trigger mode internal
        self.settings.ctrl_dtc.put(1)     # dead time corrections enabled
        self.set_rois()
        
    def _acquire_changed(self, value=None, old_value=None, **kwargs):
        #print(f"!!! HERE I AM !!!   {value}  {old_value}  {id(self._status)}  {self._status}")
        super()._acquire_changed(value=value, old_value=old_value, **kwargs)
        status = self._status
        if status is not None and status.done:
            # Clear the state to be ready for the next round.
            self._status = None
        #print(f"!!! END !!!   {value}  {old_value}  {status}  {id(self._status)}  {self._status}")
            
    def stop(self):
        ret = super().stop()
        self.hdf5.stop()
        return ret

    def stage(self):
        if self.spectra_per_point.get() != 1:
            raise NotImplementedError(
                "multi spectra per point not supported yet")
        ret = super().stage()
        self._datum_counter = itertools.count()
        return ret

    def unstage(self):
        self.settings.trigger_mode.put(0)  # 'Software'
        super().unstage()
        self._datum_counter = None
        self._status = None
        
    def set_channels_for_hdf5(self, channels=range(1,5)):
        """
        Configure which channels' data should be saved in the resulted hdf5 file.

        Parameters
        ----------
        channels: tuple, optional
            the channels to save the data for
        """
        # The number of channel
        for n in channels:
            getattr(self, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in range(1,17)]
        self.hdf5.num_extra_dims.put(0)
        self.settings.num_channels.put(len(channels))

    def reset(self):
        for i in range(1,5):
            getattr(self, f'channel{i}').reset()
            ## this doesn't work, not seeing how those arrays get cleared in the IOC....
            # getattr(self, f'mca{i}_sum').put(numpy.zeros)
            
        
    def set_roi_channel(self, channel=1, index=16, name='OCR', low=1, high=4095):
        ch = getattr(self, f'channel{channel}')
        rs = ch.rois
        this = getattr(rs, 'roi{:02}'.format(index))
        this.value.name = name
        this.bin_low.put(low)
        this.bin_high.put(high)
        

    # def ini2json(self):
    #     rj = {'OCR': {'k':  {'low': 1, 'high': 4095}},}
    #     config = configparser.ConfigParser()
    #     startup_dir = get_ipython().profile_dir.startup_dir
    #     config.read_file(open(os.path.join(startup_dir, 'rois.ini')))
    #     for i in range(20, 93):
    #         el = element_symbol(i)
    #         bounds = config.get('rois', el).split(' ')
    #         if bounds[0] == '0':
    #             rj[el] = {}
    #             continue
    #         if len(bounds) == 2:
    #             bounds.append(0)
    #             bounds.append(0)
    #         if i < 46:
    #             rj[el] = {'k':  {'low': int(bounds[0]), 'high': int(bounds[1])}}
    #         else:
    #             rj[el] = {'l3': {'low': int(bounds[0]), 'high': int(bounds[1])},
    #                       'l2': {'low': int(bounds[2]), 'high': int(bounds[3])},
    #                       'l1': {'low': 0             , 'high': 0}, }
    #     with open(os.path.join(startup_dir, 'rois.json'), 'w') as fp:
    #         json.dump(rj, fp, indent=4)
                
    def roi_details(self):
        BMMuser = user_ns['BMMuser']
        print(' ROI  Elem   low   high')
        print('==========================')
        template = ' %3d  %-4s  %4d  %4d'
        for i, el in enumerate(self.slots):
            rs = self.channel1.rois
            this = getattr(rs, 'roi{:02}'.format(i+1))
            if el is None:
                print(template % (i+1, 'None', this.bin_low.value, this.bin_high.value))
            elif el == BMMuser.element:
                print(go_msg(template % (i+1, el.capitalize(), this.bin_low.value, this.bin_high.value)))
            else:
                print(template % (i+1, el.capitalize(), this.bin_low.value, this.bin_high.value))
                

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


    def measure_xrf(self, exposure=1.0):
        yield from mv(self.settings.acquire_time, exposure)
        #yield from count([self], 1)
        yield from mv(self.settings.acquire.put,  1)
        self.table()
        self.plot(add=True)
    
        
