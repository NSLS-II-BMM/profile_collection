from bluesky import __version__ as bluesky_version
from ophyd import Component as Cpt
from ophyd import EpicsSignal
from ophyd.areadetector import Xspress3Detector

import numpy, h5py, math
import pandas as pd
import itertools, os, json

from nslsii.areadetector.xspress3 import build_detector_class

import matplotlib.pyplot as plt
from IPython import get_ipython
from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.db            import file_resource
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import now
from BMM.metadata      import mirror_state
from BMM.periodictable import Z_number
from BMM.xspress3      import Xspress3FileStoreFlyable, BMMXspress3DetectorBase, BMMXspress3Channel




################################################################################
# Notes:
#
# Before every count or scan, must explicitly set the number of points in the
# measurement:
#   xs.total_points.put(5) 
#
# This means that Xspress3 will require its own count plan
# also that a linescan or xafs scan must set total_points up front

# JOSH: I wish someone had put that note in nslsii.detector.xspress3.py


# JOSH: maybe with the new ophyd classes this class
#       does not need to know it has 4 channels?
class BMMXspress3Detector_4Element_Base(BMMXspress3DetectorBase):
    '''Subclass of BMMXspress3DetectorBase with things specific to the 4-element interface.
    '''

    #channel1 = Cpt(BMMXspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    #channel2 = Cpt(BMMXspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    #channel3 = Cpt(BMMXspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    #channel4 = Cpt(BMMXspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    #create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    #mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')
    #mca2_sum = Cpt(EpicsSignal, 'ARRSUM2:ArrayData')
    #mca3_sum = Cpt(EpicsSignal, 'ARRSUM3:ArrayData')
    #mca4_sum = Cpt(EpicsSignal, 'ARRSUM4:ArrayData')
    
    #mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')
    #mca2 = Cpt(EpicsSignal, 'ARR2:ArrayData')
    #mca3 = Cpt(EpicsSignal, 'ARR3:ArrayData')
    #mca4 = Cpt(EpicsSignal, 'ARR4:ArrayData')
    
    
    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        # if configuration_attrs is None:
        #     configuration_attrs = ['external_trig', 'total_points',
        #                            'spectra_per_point', 'settings',
        #                            'rewindable']
        if read_attrs is None:
            #read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5']
            # JOSH: Xspress3Trigger.trigger will handle generate_datum for channels
            read_attrs = ['hdf5']
        super().__init__(prefix, configuration_attrs=None,
                         read_attrs=read_attrs, **kwargs)
        # JOSH: do we need to look at this?
        self.set_channels_for_hdf5(channels=range(1,5))

        
    def reset(self):
        '''call the signals to clear ROIs.  Would like to clear array sums as well....
        '''
        # JOSH: proposed change for new xspress3 IOC
        for channel in self.iterate_channels():
            # this probably still doesn't work
            channel.mca_sum.array_data.put(numpy.zeros)
        # maybe this is how to erase the mca_sum arrays
        self.erase.put(1)

        # for i in range(1,5):
            # getattr(self.channels, f'channel_{i}').reset()
            ## this doesn't work, not seeing how those arrays get cleared in the IOC....
            # getattr(self, f'mca{i}_sum').put(numpy.zeros)
        
    def restart(self):
        # JOSH: proposed change for new xspress3 IOC
        # the PVs are different now so this is not correct
        # the new IOC enables these by default
        # maybe vis_enabled is also missing from the new IOC
        # for channel in self.iterate_channels():
        #     channel.vis_enabled.put(1)
        #     channel.extra_rois.enabled.put(1)

        # for n in range(1,5):
        #     this = getattr(self.channels, f'channel_{n}')
        #     this.vis_enabled.put(1)
        #     this.extra_rois_enabled.put(1)
        #XF:06BM-ES{Xsp:1}:C1_PluginControlValExtraROI
        super().restart()
        
    def set_rois(self):
        '''Read ROI values from a JSON serialization on disk and set all 16 ROIs for channels 1-4.
        '''
        startup_dir = get_ipython().profile_dir.startup_dir
        with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
            js = fl.read()
        allrois = json.loads(js)
        for i, el in enumerate(self.slots):
            if el == 'OCR':
                # JOSH: proposed change for new IOC
                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=i+1)
                    self.set_roi(
                        mcaroi,
                        name='OCR',
                        min_x=allrois['OCR']['low'],
                        size_x=allrois['OCR']['high'] - allrois['OCR']['low']
                    )
                # for ch in range(1,5):
                #     self.set_roi_channel(channel=ch, index=i+1, name='OCR', low=allrois['OCR']['low'], high=allrois['OCR']['high'])
                
                continue
            elif el is None:
                continue
            edge = 'k'
            if Z_number(el) > 45:
                edge = 'l3'
            # JOSH: proposed change for new IOC
            #print("getting ready to rename mcarois")
            for channel in self.iterate_channels():
                mcaroi = channel.get_mcaroi(mcaroi_number=i+1)
                #print(f"element: {el} edge: {edge} mcaroi number: {mcaroi.mcaroi_number} ")
                self.set_roi(
                    mcaroi,
                    name=f'{el.capitalize()}{channel.channel_number}',
                    min_x=allrois[el][edge]['low'],
                    size_x=allrois[el][edge]['high'] - allrois[el][edge]['low']
                )
            # for ch in range(1,5):
            #     self.set_roi_channel(channel=ch, index=i+1, name=f'{el.capitalize()}{ch}', low=allrois[el][edge]['low'], high=allrois[el][edge]['high'])
                    
    def measure_roi(self):
        '''Hint the ROI currently in use for XAS
        '''
        BMMuser = user_ns['BMMuser']
        
        # JOSH: proposed change for new IOC
        for channel in self.iterate_channels():
            for mcaroi in channel.iterate_mcarois():
                if self.slots[mcaroi.mcaroi_number-1] == BMMuser.element:
                    mcaroi.total_rbv.kind = 'hinted'
                    setattr(BMMuser, f'xs{channel.channel_number}', mcaroi.total_rbv.name) 
                    setattr(BMMuser, f'xschannel{channel.channel_number}', mcaroi.total_rbv) 
                else:
                    mcaroi.total_rbv.kind = 'omitted'

        # for i in range(16): for n in range(1,5): ch = getattr(self,
        # f'channel{n}') this = getattr(ch.rois, 'roi{:02}'.format(i+1)) if
        # self.slots[i] == BMMuser.element: this.value.kind = 'hinted'
        # setattr(BMMuser, f'xs{n}', this.value.name) setattr(BMMuser,
        # f'xschannel{n}', this.value) else: this.value.kind = 'omitted'

    def plot(self, uid=None, add=False, only=None): 
        '''Make a plot appropriate for the 4-element detector.

        The default is to overplot the four channels.
        
        Parameters
        ----------
        uid : str
            DataBroker UID. If None, use the current values in the IOC
        add : bool
            If True, plot the sum of the four channels
        only : int
            plot only the signal channel 1, 2, 3, or 4
        
        '''
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
            s2 = data_array[0][1]
            s3 = data_array[0][2]
            s4 = data_array[0][3]
        except Exception as e:
            if uid is not None: print(e)
            plt.title('XRF Spectrum')
            # JOSH: proposed change for new IOC
            s1 = self.channels.channel01.mca.array_data.get()
            s2 = self.channels.channel02.mca.array_data.get()
            s3 = self.channels.channel03.mca.array_data.get()
            s4 = self.channels.channel04.mca.array_data.get()

            # s1 = self.mca1.value
            # s2 = self.mca2.value
            # s3 = self.mca3.value
            # s4 = self.mca4.value
        e = numpy.arange(0, len(s1)) * 10
        if only is not None and only in (1, 2, 3, 4):
            # JOSH: proposed change for new IOC
            channel = self.get_channel(number=only)
            this = channel.mca.array_data

            # this = getattr(self, f'mca{only}')
            plt.plot(e, this.get(), label=f'channel {only}')
            plt.legend()
        elif add is True:
            plt.plot(e, s1+s2+s3+s4, label='sum of four channels')
            plt.legend()
        else:
            plt.plot(e, s1, label='channel 1')
            plt.plot(e, s2, label='channel 2')
            plt.plot(e, s3, label='channel 3')
            plt.plot(e, s4, label='channel 4')
            plt.legend()
        plt.show()
            
    def table(self):
        '''Pretty print a table of values for each ROI and for all four channels.
        '''
        BMMuser = user_ns['BMMuser']
        print(' ROI    Chan1      Chan2      Chan3      Chan4 ')
        print('=================================================')
        first_channel_number = self.channel_numbers[0]
        first_channel = self.get_channel(channel_number=first_channel_number)
        for r in first_channel.mcaroi_numbers:
            # JOSH: proposed change for new IOC
            el = self.channels.channel01.get_mcaroi(mcaroi_number=r).name
            #el = getattr(self.channels.channel01.mcarois, f"mcaroi{r:02}").roi_name.get()
            #el = getattr(self.channel1.rois, f'roi{r:02}').value.name
            if len(el) > 3:
                continue
            if el != 'OCR':
                el = el[:-1]
            if '_value' in el:
                print(' None', end='')
                for channel_number in self.channel_numbers:
                    print(f"  {0:7}  ", end='')
                #for c in (1,2,3,4):
                #    print(f"  {0:7}  ", end='')
                print('')
            elif el == BMMuser.element or el == 'OCR':
                print(go_msg(f' {el:3} '), end='')
                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=r)
                    val = mcaroi.total_rbv.get()
                    if math.isnan(val):
                        val = 0
                    print(go_msg(f"  {int(val):7}  "), end='')
                #for c in (1,2,3,4):
                #    val = getattr(getattr(self, f'channel{c:02}').rois, f'roi{r:02}').value.get()
                #    if math.isnan(val):
                #        val = 0
                #    print(go_msg(f"  {int(val):7}  "), end='')
                
                print('')
            else:                
                print(f' {el:3} ', end='')

                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=r)
                    val = mcaroi.total_rbv.get()
                    if math.isnan(val):
                        val = 0
                    print(f"  {int(val):7}  ", end='')
                
                #for c in (1,2,3,4):
                #    val = getattr(getattr(self, f'channel{c:02}').rois, f'roi{r:02}').value.get()
                #    if math.isnan(val):
                #        val = 0
                #    print(f"  {int(val):7}  ", end='')
                print('')


    def to_xdi(self, filename=None):
        '''Write an XDI-style file with bin energy in the first column and the
        waveform of each of the 4 channels in the other columns.

        '''
        dcm, BMMuser, ring = user_ns['dcm'], user_ns['BMMuser'], user_ns['ring']

        column_list = ['MCA1', 'MCA2', 'MCA3', 'MCA4']
        column_list = [f'MCA{channel_number}' for channel_number in self.channel_numbers]
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
        handle.write('# Scan.dwell_time: %.2f\n'             % self.cam.acquire_time.value)
        handle.write('# Facility.name: NSLS-II\n')
        handle.write('# Facility.current: %.1f mA\n'         % ring.current.value)
        handle.write('# Facility.mode: %s\n'                 % ring.mode.value)
        handle.write('# Facility.cycle: %s\n'                % BMMuser.cycle)
        handle.write('# Facility.GUP: %d\n'                  % BMMuser.gup)
        handle.write('# Facility.SAF: %d\n'                  % BMMuser.saf)
        handle.write('# Column.1: energy (eV)\n')
        for c, mca_number in enumerate(column_list):
            handle.write(f'# Column.{c+2}: MCA{mca_number} (counts)\n')
        #handle.write('# Column.2: MCA1 (counts)\n')
        #handle.write('# Column.3: MCA2 (counts)\n')
        #handle.write('# Column.4: MCA3 (counts)\n')
        #handle.write('# Column.5: MCA4 (counts)\n')
        handle.write('# ==========================================================\n')
        handle.write('# energy ')

        ## data table
        e=numpy.arange(0, len(self.channels.channel01.mca.array_data.get())) * 10
        # JOSH: proposal for new xspress3 
        mca_data_array_list = [channel.mca.array_data.get() for channel in self.iterate_channels()]
        a=numpy.vstack(mca_data_array_list)
        # a=numpy.vstack([self.mca1.value, self.mca2.value, self.mca3.value, self.mca4.value])
        b=pd.DataFrame(a.transpose(), index=e, columns=column_list)
        handle.write(b.to_csv(sep=' '))

        handle.flush()
        handle.close()
        print(bold_msg('wrote XRF spectra to %s' % filename))


BMMXspress3Detector_4Element = build_detector_class(
    channel_numbers=(1, 2, 3, 4),
    mcaroi_numbers=range(1, 17),
    detector_parent_classes=(BMMXspress3Detector_4Element_Base, )
)
