
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
from ophyd import Signal, EpicsSignal, EpicsSignalRO
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

from BMM.xspress3_4element import Xspress3FileStoreFlyable, BMMXspress3Channel

    
class BMMXspress3Detector_1Element(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel8 = Cpt(BMMXspress3Channel, 'C8_', channel_num=8, read_attrs=['rois'])
    #create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    mca8_sum = Cpt(EpicsSignal, 'ARRSUM8:ArrayData')
    
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
            read_attrs = ['channel8', 'hdf5']
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
        
    def set_channels_for_hdf5(self, channels=(8,)):
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
        #self.settings.num_channels.put(len(channels))
        self.settings.num_channels.put(8)

    def reset(self):
        self.channel8.reset()
        ## this doesn't work, not seeing how those arrays get cleared in the IOC....
        # getattr(self, f'mca{i}_sum').put(numpy.zeros)
            
        
    def set_roi_channel(self, channel=8, index=16, name='OCR', low=1, high=4095):
        ch = getattr(self, f'channel{channel}')
        rs = ch.rois
        this = getattr(rs, 'roi{:02}'.format(index))
        this.value.name = name
        this.bin_low.put(low)
        this.bin_high.put(high)
        
    def set_rois(self):
        startup_dir = get_ipython().profile_dir.startup_dir
        with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
            js = fl.read()
        allrois = json.loads(js)
        for i, el in enumerate(self.slots):
            if el == 'OCR':
                self.set_roi_channel(channel=8, index=i+1, name='OCR', low=allrois['OCR']['low'], high=allrois['OCR']['high'])
                continue
            elif el is None:
                continue
            edge = 'k'
            if Z_number(el) > 46:
                edge = 'l3'
            self.set_roi_channel(channel=8, index=i+1, name=f'{el.capitalize()}8', low=allrois[el][edge]['low'], high=allrois[el][edge]['high'])
                    
                
    def roi_details(self):
        BMMuser = user_ns['BMMuser']
        print(' ROI  Elem   low   high')
        print('==========================')
        template = ' %3d  %-4s  %4d  %4d'
        for i, el in enumerate(self.slots):
            rs = self.channel8.rois
            this = getattr(rs, 'roi{:02}'.format(i+1))
            if el is None:
                print(template % (i+1, 'None', this.bin_low.value, this.bin_high.value))
            elif el == BMMuser.element:
                print(go_msg(template % (i+1, el.capitalize(), this.bin_low.value, this.bin_high.value)))
            else:
                print(template % (i+1, el.capitalize(), this.bin_low.value, this.bin_high.value))
                
    def measure_roi(self):
        BMMuser = user_ns['BMMuser']
        for i in range(16):
            this = getattr(self.channel8.rois, 'roi{:02}'.format(i+1))
            if self.slots[i] == BMMuser.element:
                this.value.kind = 'hinted'
                BMMuser.xs8 = this.value.name
                BMMuser.xschannel8 = this.value
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


    def measure_xrf(self, exposure=1.0):
        yield from mv(self.settings.acquire_time, exposure)
        #yield from count([self], 1)
        yield from mv(self.settings.acquire.put,  1)
        self.table()
        self.plot(add=True)
    
    def plot(self, uid=None, add=False, only=None):
        dcm = user_ns['dcm']
        plt.clf()
        plt.xlabel('Energy  (eV)')
        plt.ylabel('counts')
        plt.grid(which='major', axis='both')
        plt.xlim(2500, round(dcm.energy.position, -2)+500)
        try:
            #print(f'{uid}')
            fname = file_resource(uid)
            db = user_ns['db']
            plt.title(db.v2[uid].metadata['start']['XDI']['Sample']['name'])
            f = h5py.File(fname,'r')
            g = f['entry']['instrument']['detector']['data']
            data_array = g.value
            s1 = data_array[0][0]
        except Exception as e:
            print(e)
            plt.title('XRF Spectrum')
            s1 = self.mca8.value
        e = numpy.arange(0, len(s1)) * 10
        plt.plot(e, s1, label='channel 8')
        plt.legend()

    def table(self):
        BMMuser = user_ns['BMMuser']
        print(' ROI    Chan1 ')
        print('================')
        for r in range(1,17):
            el = getattr(self.channel8.rois, f'roi{r:02}').value.name
            if len(el) > 3:
                continue
            if el != 'OCR':
                el = el[:-1]
            if el == BMMuser.element or el == 'OCR':
                print(go_msg(f' {el:3} '), end='')
                for c in (8,):
                    print(go_msg(f"  {int(getattr(getattr(self, f'channel{c}').rois, f'roi{r:02}').value.get()):7}  "), end='')
                print('')
            else:                
                print(f' {el:3} ', end='')
                for c in (8,):
                    print(f"  {int(getattr(getattr(self, f'channel{c}').rois, f'roi{r:02}').value.get()):7}  ", end='')
                print('')

    def to_xdi(self, filename=None):

        dcm, BMMuser, ring = user_ns['dcm'], user_ns['BMMuser'], user_ns['ring']

        column_list = ['MCA8']
        #template = "  %.3f  %.6f  %.6f  %.6f  %.6f\n"
        m2state, m3state = mirror_state()

        handle = open(filename, 'w')
        handle.write('# XDI/1.0 BlueSky/%s\n'                % bluesky_version)
        #handle.write('# Scan.uid: %s\n'          % dataframe['start']['uid'])
        #handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
        handle.write('# Beamline.name: BMM (06BM) -- Beamline for Materials Measurement')
        handle.write('# Beamline.xray_source: NSLS-II three-pole wiggler\n')
        handle.write('# Beamline.collimation: paraboloid mirror, 5 nm Rh on 30 nm Pt\n')
        handle.write('# Beamline.focusing: %s\n'             % m2state)
        handle.write('# Beamline.harmonic_rejection: %s\n'   % m3state)
        handle.write('# Beamline.energy: %.3f\n'             % dcm.energy.position)
        handle.write('# Detector.fluorescence: SII Vortex ME4 (4-element silicon drift)\n')
        handle.write('# Scan.end_time: %s\n'                 % now())
        handle.write('# Scan.dwell_time: %.2f\n'             % self.settings.acquire_time.value)
        handle.write('# Facility.name: NSLS-II\n')
        handle.write('# Facility.current: %.1f mA\n'         % ring.current.value)
        handle.write('# Facility.mode: %s\n'                 % ring.mode.value)
        handle.write('# Facility.cycle: %s\n'                % BMMuser.cycle)
        handle.write('# Facility.GUP: %d\n'                  % BMMuser.gup)
        handle.write('# Facility.SAF: %d\n'                  % BMMuser.saf)
        handle.write('# Column.1: energy (eV)\n')
        handle.write('# Column.2: MCA1 (counts)\n')
        handle.write('# ==========================================================\n')
        handle.write('# energy ')

        ## data table
        e=numpy.arange(0, len(self.mca1.value)) * 10
        a=numpy.vstack([self.mca1.value, self.mca2.value, self.mca3.value, self.mca4.value])
        b=pd.DataFrame(a.transpose(), index=e, columns=column_list)
        handle.write(b.to_csv(sep=' '))

        handle.flush()
        handle.close()
        print(bold_msg('wrote XRF spectra to %s' % filename))
        
