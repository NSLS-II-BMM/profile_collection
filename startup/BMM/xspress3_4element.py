from bluesky import __version__ as bluesky_version

import numpy, h5py
import pandas as pd
import itertools, os, json

import matplotlib.pyplot as plt
from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.db            import file_resource
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import now
from BMM.metadata      import mirror_state
from BMM.periodictable import Z_number
from BMM.xspress3      import Xspress3FileStoreFlyable, BMMXspress3DetectorBase

#from databroker.assets.handlers import HandlerBase, Xspress3HDF5Handler, XS3_XRF_DATA_KEY



################################################################################
# Notes:
#
# Before every count or scan, must explicitly set the number of points in the
# measurement:
#   xs.total_points.put(5) 
#
# This means that Xspress3 will require its own count plan
# also that a linescan or xafs scan must set total_points up front

class BMMXspress3Detector_4Element(BMMXspress3DetectorBase):
    '''Subclass of BMMXspress3DetectorBase with things specific to the 4-element interface.
    '''
    
    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        # if configuration_attrs is None:
        #     configuration_attrs = ['external_trig', 'total_points',
        #                            'spectra_per_point', 'settings',
        #                            'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)

        
    def set_rois(self):
        '''Read ROI values from a JSON serialization on disk and set all 16 ROIs for channels 1-4.
        '''
        startup_dir = get_ipython().profile_dir.startup_dir
        with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
            js = fl.read()
        allrois = json.loads(js)
        for i, el in enumerate(self.slots):
            if el == 'OCR':
                for ch in range(1,5):
                    self.set_roi_channel(channel=ch, index=i+1, name='OCR', low=allrois['OCR']['low'], high=allrois['OCR']['high'])
                continue
            elif el is None:
                continue
            edge = 'k'
            if Z_number(el) > 46:
                edge = 'l3'
            for ch in range(1,5):
                self.set_roi_channel(channel=ch, index=i+1, name=f'{el.capitalize()}{ch}', low=allrois[el][edge]['low'], high=allrois[el][edge]['high'])
                    
    def measure_roi(self):
        '''Hint the ROI currently in use for XAS
        '''
        BMMuser = user_ns['BMMuser']
        for i in range(16):
            for n in range(1,5):
                ch = getattr(self, f'channel{n}')
                this = getattr(ch.rois, 'roi{:02}'.format(i+1))
                if self.slots[i] == BMMuser.element:
                    this.value.kind = 'hinted'
                    setattr(BMMuser, f'xs{n}', this.value.name)
                    setattr(BMMuser, f'xschannel{n}', this.value)
                else:
                    this.value.kind = 'omitted'

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
            print(e)
            plt.title('XRF Spectrum')
            s1 = self.mca1.value
            s2 = self.mca2.value
            s3 = self.mca3.value
            s4 = self.mca4.value
        e = numpy.arange(0, len(s1)) * 10
        if only is not None and only in (1, 2, 3, 4):
            this = getattr(self, f'mca{only}')
            plt.plot(e, this.value, label=f'channel {only}')
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

    def table(self):
        '''Pretty print a table of values for each ROI and for all four channels.
        '''
        BMMuser = user_ns['BMMuser']
        print(' ROI    Chan1      Chan2      Chan3      Chan4 ')
        print('=================================================')
        for r in range(1,17):
            el = getattr(self.channel1.rois, f'roi{r:02}').value.name
            if len(el) > 3:
                continue
            if el != 'OCR':
                el = el[:-1]
            if el == BMMuser.element or el == 'OCR':
                print(go_msg(f' {el:3} '), end='')
                for c in (1,2,3,4):
                    print(go_msg(f"  {int(getattr(getattr(self, f'channel{c}').rois, f'roi{r:02}').value.get()):7}  "), end='')
                print('')
            else:                
                print(f' {el:3} ', end='')
                for c in (1,2,3,4):
                    print(f"  {int(getattr(getattr(self, f'channel{c}').rois, f'roi{r:02}').value.get()):7}  ", end='')
                print('')


    def to_xdi(self, filename=None):
        '''Write an XDI-style file with bin energy in the first column and the
        waveform of each of the 4 channels in the other columns.

        '''
        dcm, BMMuser, ring = user_ns['dcm'], user_ns['BMMuser'], user_ns['ring']

        column_list = ['MCA1', 'MCA2', 'MCA3', 'MCA4']
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
        handle.write('# Column.3: MCA2 (counts)\n')
        handle.write('# Column.4: MCA3 (counts)\n')
        handle.write('# Column.5: MCA4 (counts)\n')
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
        
