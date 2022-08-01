from bluesky import __version__ as bluesky_version
from ophyd import Component as Cpt
from ophyd import EpicsSignal
from ophyd.areadetector import Xspress3Detector

import numpy, h5py, math
import pandas
import itertools, os, json
import xraylib

from nslsii.areadetector.xspress3 import build_detector_class

import matplotlib.pyplot as plt

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

#from BMM.db            import file_resource
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import now
from BMM.metadata      import mirror_state
from BMM.periodictable import Z_number, edge_number
from BMM.xspress3      import Xspress3FileStoreFlyable, BMMXspress3DetectorBase, BMMXspress3Channel

from BMM.user_ns.base import startup_dir, bmm_catalog



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
class BMMXspress3Detector_4Element_Base(BMMXspress3DetectorBase):
    '''Subclass of BMMXspress3DetectorBase with things specific to the 4-element interface.
    '''

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ['hdf5']
        super().__init__(prefix, configuration_attrs=None,
                         read_attrs=read_attrs, **kwargs)
        self.hdf5.num_extra_dims.put(0)
        
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
        dcm, BMMuser = user_ns['dcm'], user_ns['BMMuser']
        plt.clf()
        plt.xlabel('Energy  (eV)')
        plt.ylabel('counts')
        plt.grid(which='major', axis='both')
        plt.xlim(2500, round(dcm.energy.position, -2)+500)
        try:
            record = bmm_catalog[uid]
            #print(f'{uid}')
            # fname = file_resource(uid)
            # db = user_ns['db']
            plt.title(record.metadata['start']['XDI']['Sample']['name'])
            # f = h5py.File(fname,'r')
            # g = f['entry']['instrument']['detector']['data']
            # data_array = g.value
            # s1 = data_array[0][0]
            # s2 = data_array[0][1]
            # s3 = data_array[0][2]
            # s4 = data_array[0][3]
            s1 = record['primary']['data']['xs_channels_channel01'][0]
            s2 = record['primary']['data']['xs_channels_channel02'][0]
            s3 = record['primary']['data']['xs_channels_channel03'][0]
            s4 = record['primary']['data']['xs_channels_channel04'][0]
        except Exception as e:
            if uid is not None: print(e)
            plt.title('XRF Spectrum')
            s1 = self.channel01.mca.array_data.get()
            s2 = self.channel02.mca.array_data.get()
            s3 = self.channel03.mca.array_data.get()
            s4 = self.channel04.mca.array_data.get()
        e = numpy.arange(0, len(s1)) * 10
        if only is not None and only in (1, 2, 3, 4):
            channel = self.get_channel(number=only)
            this = channel.mca.array_data

            # this = getattr(self, f'mca{only}')
            plt.ion()
            plt.plot(e, this.get(), label=f'channel {only}')
            plt.legend()
        elif add is True:
            plt.ion()
            plt.plot(e, s1+s2+s3+s4, label='sum of four channels')
            plt.legend()
        else:
            plt.ion()
            plt.plot(e, s1, label='channel 1')
            plt.plot(e, s2, label='channel 2')
            plt.plot(e, s3, label='channel 3')
            plt.plot(e, s4, label='channel 4')
            plt.legend()
        z = Z_number(BMMuser.element)
        if BMMuser.edge.lower() == 'k':
            plt.axvline(x = xraylib.LineEnergy(z, xraylib.KL3_LINE)*1000,  color = 'brown', linewidth=1)
        elif BMMuser.edge.lower() == 'l3':
            plt.axvline(x = xraylib.LineEnergy(z, xraylib.L3M5_LINE)*1000, color = 'brown', linewidth=1)
        elif BMMuser.edge.lower() == 'l2':
            plt.axvline(x = xraylib.LineEnergy(z, xraylib.L2M4_LINE)*1000, color = 'brown', linewidth=1)
        elif BMMuser.edge.lower() == 'l1':
            plt.axvline(x = xraylib.LineEnergy(z, xraylib.L1M3_LINE)*1000, color = 'brown', linewidth=1)
        #plt.show()
            
    def table(self):
        '''Pretty print a table of values for each ROI and for all four channels.
        '''
        BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']

        edge = xraylib.EdgeEnergy(Z_number(BMMuser.element), int(edge_number(BMMuser.edge)))*1000

        if dcm.energy.position > edge:
            print(f'{BMMuser.element} {BMMuser.edge} -- current energy: {round(dcm.energy.position, 1)}\n')
        else:
            print(warning_msg(f'{BMMuser.element} {BMMuser.edge} -- current energy: {round(dcm.energy.position, 1)}  *** Below Edge! ***\n'))
        print(' ROI    Chan1      Chan2      Chan3      Chan4 ')
        print('=================================================')
        first_channel_number = self.channel_numbers[0]
        first_channel = self.get_channel(channel_number=first_channel_number)
        for r in first_channel.mcaroi_numbers:
            el = self.channel01.get_mcaroi(mcaroi_number=r).name
            if len(el) > 3:
                continue
            if el != 'OCR':
                el = el[:-1]
            if '_value' in el:
                print(' None', end='')
                for channel_number in self.channel_numbers:
                    print(f"  {0:7}  ", end='')
                print('')
            elif el == BMMuser.element or el == 'OCR':
                if dcm.energy.position > edge:
                    print(go_msg(f' {el:3} '), end='')
                else:
                    print(warning_msg(f' {el:3} '), end='')                    
                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=r)
                    val = mcaroi.total_rbv.get()
                    if math.isnan(val):
                        val = 0
                    if dcm.energy.position > edge:
                        print(go_msg(f"  {int(val):7}  "), end='')
                    else:
                        print(warning_msg(f"  {int(val):7}  "), end='')
                        
                print('')
            else:                
                print(f' {el:3} ', end='')

                for channel in self.iterate_channels():
                    mcaroi = channel.get_mcaroi(mcaroi_number=r)
                    val = mcaroi.total_rbv.get()
                    if math.isnan(val):
                        val = 0
                    print(f"  {int(val):7}  ", end='')
                print('')


    def to_xdi(self, filename=None):
        '''Write an XDI-style file with bin energy in the first column and the
        waveform of each of the 4 channels in the other columns.

        '''
        dcm, BMMuser, ring = user_ns['dcm'], user_ns['BMMuser'], user_ns['ring']

        column_list = ['MCA1', 'MCA2', 'MCA3', 'MCA4']
        column_list = [f'MCA{channel_number}' for channel_number in self.channel_numbers]
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
        handle.write('# ==========================================================\n')
        handle.write('# energy ')

        ## data table
        e=numpy.arange(0, len(self.channel01.mca.array_data.get())) * 10
        mca_data_array_list = [channel.mca.array_data.get() for channel in self.iterate_channels()]
        a=numpy.vstack(mca_data_array_list)
        b=pandas.DataFrame(a.transpose(), index=e, columns=column_list)
        handle.write(b.to_csv(sep=' '))

        handle.flush()
        handle.close()
        print(bold_msg('wrote XRF spectra to %s' % filename))


BMMXspress3Detector_4Element = build_detector_class(
    channel_numbers=(1, 2, 3, 4),
    mcaroi_numbers=range(1, 17),
    detector_parent_classes=(BMMXspress3Detector_4Element_Base, )
)
