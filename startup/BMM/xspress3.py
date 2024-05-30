import numpy, h5py, json
import itertools, os, sys
import time as ttime
from collections import deque, OrderedDict
from itertools import product
from tqdm import tqdm

from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin, Xspress3Detector)
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
from ophyd import Component as Cpt #, set_and_wait
from ophyd.utils import set_and_wait
from bluesky import __version__ as bluesky_version
from bluesky.plans import count
from bluesky.plan_stubs import sleep, mv, null

from pathlib import PurePath
from nslsii.detectors.xspress3 import Xspress3Channel
from nslsii.areadetector.xspress3 import Xspress3Trigger, Xspress3FileStore

# deal with HDF5 storage as of January 2023
if sys.version_info[1] > 9:
    from nslsii.areadetector.xspress3 import Xspress3HDF5Plugin


import matplotlib.pyplot as plt

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)
md = user_ns["RE"].md

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM.periodictable import Z_number

from BMM.user_ns.base import startup_dir

        
from databroker.assets.handlers import HandlerBase, Xspress3HDF5Handler, XS3_XRF_DATA_KEY




################################################################################
# Notes:
#
# Before every count or scan, must explicitly set the number of points in the
# measurement:
#   xs.total_points.put(5) 
#
# This means that Xspress3 will require its own count plan
# also that a linescan or xafs scan must set total_points up front

#class Xspress3FileStoreFlyable(Xspress3FileStore):
class BMMXspress3HDF5Plugin(Xspress3HDF5Plugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs["root_path"] is None or kwargs["path_template"] is None:
            self._update_paths()

    def _update_paths(self):
        self.root_path.put(self.root_path_str)
        self.path_template.put(self.path_template_str)

    @property
    def root_path_str(self):
        root_path = f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/xspress3-1/"
        return root_path

    @property
    def path_template_str(self):
        path_template = "%Y/%m/%d"
        return path_template

    def stage(self, *args, **kwargs):
        self._update_paths()
        super().stage(*args, **kwargs)

    def warmup(self):
        """
        A convenience method for 'priming' the plugin.
        The plugin has to 'see' one acquisition before it is ready to capture.
        This sets the array size, etc.
        NOTE : this comes from:
            https://github.com/NSLS-II/ophyd/blob/master/ophyd/areadetector/plugins.py
        We had to replace "cam" with "settings" here.

        This has been slightly modified by Bruce to avoid a situation where the warmup
        hangs.  Also to add some indication on screen for what is happening.
        """
        print(whisper("                        warming up the hdf5 plugin..."), flush=True)
        self.enable.set(1).wait()

        # JOSH: proposed changes for new IOC
        sigs = OrderedDict([(self.parent.cam.array_callbacks, 1),
                            (self.parent.cam.image_mode, "Single"),
                            (self.parent.cam.trigger_mode, 'Internal'),
                            # just in case the acquisition time is set very long...
                            (self.parent.cam.acquire_time, 0.2),
                            (self.parent.cam.num_images, 1),
                            #(self.parent.cam.acquire, 1)
                        ]
        )

        original_vals = {sig: sig.get() for sig in sigs}

        # Remove the hdf5.capture item here to avoid an error as it should reset back to 0 itself
        # del original_vals[self.capture]

        for sig, val in sigs.items():
            sig.set(val).wait()
            ttime.sleep(0.1)  # abundance of caution

        self.parent.cam.acquire.set(1).wait()
        
        # JOSH: do we need more than 2 seconds here?
        #       adding more time here helps!
        for i in tqdm(range(4), colour='#7f8c8d'):
            ttime.sleep(0.5)  # wait for acquisition

        for sig, val in reversed(list(original_vals.items())):
            ttime.sleep(0.1)
            sig.set(val).wait()
        print(whisper("                        done"))

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
    '''Subclass of Xspress3Channel to capture the reset PVs for each ROI
    in a channel
    '''
    extra_rois_enabled = Cpt(EpicsSignal, 'PluginControlValExtraROI')
    resets = DDCpt(_reset_fields('reset', 'Reset', range(1, 17)))
    def reset(self):
        for r in self.resets.read_attrs:
            getattr(self.resets, r).put(1)
################################################################################


# JL: Xspress3Trigger before Xspress3Detector means Xspress3Trigger.trigger() is called
class BMMXspress3DetectorBase(Xspress3Trigger, Xspress3Detector):
    '''This class captures everything that is in common for the 1-element
    and 4-element detector interfaces.
    '''

    # if sys.version_info[1] < 10:
    #     ## HDF5 storage semantics prior to January 2023
    #     hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF1:',
    #                read_path_template='/nsls2/data3/bmm/assets/xspress3/2022',  # path to data folder, as mounted on client (i.e. Lustre) 
    #                root='/nsls2/data3/bmm/',                                    # path to root, as mounted on client (i.e. Lustre)
    #                write_path_template='/nsls2/data3/bmm/assets/xspress3/2022', # full path on IOC server (i.e. xf06bm-xspress3)
    #                )
    # else:
        ## new HDF5 storage semantics as of January 2023



    hdf5 = Cpt(BMMXspress3HDF5Plugin,
               "HDF1:", 
               name="h5p",
               root_path=None,
               path_template=None,
               resource_kwargs={},
    )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'cam',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel01', 'channel02', 'channel03', 'channel04', 'hdf5'] #, 'channel8'
            #, 'channel5', 'channel6', 'channel7', 'channel8'
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)

        self._asset_docs_cache = deque()
        self._datum_counter = None
        
        self.slots = ['Ti', 'V',  'Cr', 'Mn',
                      'Fe', 'Co', 'Ni', 'Cu',
                      'Zn', 'Ge', 'As', 'Br',
                      'Nb', 'Mo', None, 'OCR']
        self.restart()

    # JL: trying to use Xspress3Trigger.trigger
    #     which is almost identical to this
    def trigger_hide(self):
        if self._staged != Staged.yes:
            raise RuntimeError("not staged")

        import epics
        #t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
        #print('tr1 {} '.format(t))
        self._status = DeviceStatus(self)
        self.cam.acquire.put(1, wait=False)
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
        self.cam.num_images.put(1)
        self.cam.trigger_mode.put(1)
        self.cam.ctrl_dtc.put(1)
        self.set_rois()
        
    def _acquire_changed_hide(self, value=None, old_value=None, **kwargs):
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
        self.cam.trigger_mode.put(0)
        super().unstage()
        self._datum_counter = None
        self._status = None

    def reset(self):
        '''call the signals to clear ROIs.  Would like to clear array sums as well....
        '''
        for channel in self.iterate_channels():
            # this probably still doesn't work
            channel.mca_sum.array_data.put(numpy.zeros)
        self.erase.put(1)

    def describe(self):
        res = super().describe()
        try:
            res['4-element SDD_channel01_xrf']['dtype_str'] = '<f8'
            res['4-element SDD_channel02_xrf']['dtype_str'] = '<f8'
            res['4-element SDD_channel03_xrf']['dtype_str'] = '<f8'
            res['4-element SDD_channel04_xrf']['dtype_str'] = '<f8'
        except:
            pass
        try:
            res['1-element SDD_channel08_xrf']['dtype_str'] = '<f8'
        except:
            pass            
        return res

    def set_rois(self):
        '''Read ROI values from a JSON serialization on disk and set all 16 ROIs for channels 1-4.
        '''
        with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
            js = fl.read()
        allrois = json.loads(js)
        for i, el in enumerate(self.slots):
            if el == 'OCR':
                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=i+1)
                    self.set_roi(
                        mcaroi,
                        name='OCR',
                        min_x=allrois['OCR']['low'],
                        size_x=allrois['OCR']['high'] - allrois['OCR']['low']
                    )
                
                continue
            elif el is None:
                continue
            edge = 'k'
            if Z_number(el) > 45:
                edge = 'l3'
            if el == user_ns['BMMuser'].element:
                edge = user_ns['BMMuser'].edge.lower()
            for channel in self.iterate_channels():
                mcaroi = channel.get_mcaroi(mcaroi_number=i+1)
                #print(f"element: {el} edge: {edge} mcaroi number: {mcaroi.mcaroi_number} ")
                self.set_roi(
                    mcaroi,
                    name=f'{el.capitalize()}{channel.channel_number}',
                    min_x=allrois[el][edge]['low'],
                    size_x=allrois[el][edge]['high'] - allrois[el][edge]['low']
                )
                # Azure testing error happens at this line ^

    def measure_roi(self):
        '''Hint the ROI currently in use for XAS
        '''
        BMMuser = user_ns['BMMuser']
        for channel in self.iterate_channels():
            for mcaroi in channel.iterate_mcarois():
                if self.slots[mcaroi.mcaroi_number-1] == BMMuser.element:
                    mcaroi.kind = 'hinted'
                    mcaroi.total_rbv.kind = 'hinted'
                    setattr(BMMuser, f'xs{channel.channel_number}', mcaroi.total_rbv.name) 
                    setattr(BMMuser, f'xschannel{channel.channel_number}', mcaroi.total_rbv)
                elif self.slots[mcaroi.mcaroi_number-1] == 'K':
                    mcaroi.kind = 'hinted'
                    mcaroi.total_rbv.kind = 'hinted'
                # elif self.slots[mcaroi.mcaroi_number-1] == 'La':
                #     mcaroi.kind = 'hinted'
                #     mcaroi.total_rbv.kind = 'hinted'
                else:
                    mcaroi.kind = 'omitted'
                    mcaroi.total_rbv.kind = 'omitted'
        
            
    def set_roi(self, mcaroi, name='OCR', min_x=1, size_x=4095):
        """
        Combine setting PVs and setting the 'name' field of a mcaroi.
        """
        # if type(name) is bytes:
        #     name.decode('utf8')
        mcaroi.configure_mcaroi(
            roi_name=name,
            min_x=min_x,
            size_x=size_x            
        )
        mcaroi.name = name
        mcaroi.total_rbv.name = name


    def set_roi_channel(self, channel, index=16, name='OCR', low=1, high=4095):
        mcaroi = channel.get_mcaroi(mcaroi_number=index)
        mcaroi.total_rbv.name = name
        mcaroi.min_x.put(low)
        mcaroi.size_x.put(high - low)

        
    def reset_rois(self, el=None, tab='', quiet = False):
        BMMuser = user_ns['BMMuser']
        if el is None:
            el = BMMuser.element
        if el in self.slots:
            if quiet is False:
                print(whisper(f'{tab}Resetting rois with {el} as the active ROI'))
            BMMuser.element = el
            self.set_rois()
            self.measure_roi()
        else:
            print(error_msg(f'{tab}Cannot reset rois, {el} is not in {self.name}.slots'))

    def roi_details(self):
        BMMuser = user_ns['BMMuser']
        print(' ROI  Elem   low   high')
        print('==========================')
        template = ' %3d  %-4s  %4d  %4d'
        for i, el in enumerate(self.slots):
            this = self.get_channel(channel_number=1).get_mcaroi(mcaroi_number=i+1)
            if el is None:
                print(template % (i+1, 'None', this.min_x.get(), this.min_x.get() + this.size_x.get()))
            elif el == BMMuser.element:
                print(
                    go_msg(
                        template % 
                        (i+1, el.capitalize(), this.min_x.get(), this.min_x.get() + this.size_x.get())
                    )
                )
            else:
                print(
                    template % 
                    (i+1, el.capitalize(), this.min_x.get(), this.min_x.get() + this.size_x.get())
                )
                            

    def show_rois(self):
        BMMuser = user_ns['BMMuser']
        text = list_msg('Xspress3 ROIs:\n')
        text += bold_msg('    1      2      3      4      5      6      7      8\n')
        text += ' '
        for i in range(8):
            if self.slots[i] == BMMuser.element:
                text += go_msg('%4.4s' % self.slots[i]) + '   '
            else:
                text += '%4.4s' % self.slots[i] + '   '
        text += '\n\n'
        text += bold_msg('    9     10     11     12     13     14     15     16\n')
        text += ' '
        for i in range(8, 16):
            if self.slots[i] == BMMuser.element:
                text += go_msg('%4.4s' % self.slots[i]) + '   '
            else:
                text += '%4.4s' % self.slots[i] + '   '
        text += '\n'
        return(text)


    def check_element(self, element, edge):
        '''Check that the current element and edge is tabulated in rois.json
        '''
        with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
            js = fl.read()
        allrois = json.loads(js)
        if element.capitalize() not in allrois:
            #print(f'{element} is not a tabulated element')
            return False
        this = allrois[element]
        if edge.lower() not in this:
            #print(f'ROI for the {element} {edge} edge are not tabulated')
            return False
        if this[edge.lower()]['low'] == 0 or this[edge.lower()]['high'] == 0:
            #print(f'ROI for the {element} {edge} edge are not tabulated')
            return False
        return True
    

    def measure_xrf(self, exposure=1.0, doplot=True):
        uid = None
        self.total_points.put(1)
        self.cam.acquire_time.put(exposure)
        self.cam.acquire.put(1)
        ttime.sleep(exposure + 0.5)
        self.table()
        if doplot:
            self.plot(add=True, uid=uid)
        
