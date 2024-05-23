from bluesky import __version__ as bluesky_version
from ophyd import Component as Cpt
from ophyd import EpicsSignal
from ophyd.areadetector import Xspress3Detector

import numpy, h5py, math
import pandas as pd
import itertools, os, json, sys
import xraylib

if sys.version_info[1] == 9:
    from nslsii.areadetector.xspress3 import build_detector_class
else:
    from nslsii.areadetector.xspress3 import build_xspress3_class

import matplotlib.pyplot as plt

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import now
from BMM.kafka         import kafka_message
from BMM.metadata      import mirror_state
from BMM.periodictable import Z_number, edge_number
from BMM.xspress3      import BMMXspress3DetectorBase, BMMXspress3Channel

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


class BMMXspress3Detector_1Element_Base(BMMXspress3DetectorBase):
    '''Subclass of BMMXspress3DetectorBase with things specific to the 1-element interface.
    '''

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ['hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.slots = ['Ti', 'V',  'Cr', 'Mn',
                      'Fe', 'Co', 'Ni', 'Cu',
                      'Zn', 'Ge', 'As', 'Br',
                      'Nb', 'K', None, 'OCR']
        self.hdf5.num_extra_dims.put(0)
        
        ## May 22, 2024: this PV suppresses the EraseOnStart function
        ## of the Xspress3 IOC.  When on and used in the way BMM uses
        ## the IOC, this leads to trouble in the form of a "ghost
        ## frame" whenever the Xspress3 is counted.  This confuses a
        ## simple count, and also adss considerable overhead to an
        ## XAFS scan.  These two lines force that PV to off in a way
        ## that is intentionally hidden.
        erase_on_start = EpicsSignal('XF:06BM-ES{Xsp:1}:det1:EraseOnStart', name='erase_on_start')
        erase_on_start.put(0)
        
    
    def plot(self, uid=None, add=False, only=None):
        '''Make a plot appropriate for the 4-element detector.

        Parameters
        ----------
        uid : str
            DataBroker UID. If None, use the current values in the IOC
        add : bool
            ignored, included for consistency with 4-element interface
        only : int
            ignored, included for consistency with 4-element interface
        
        '''
        if uid is not None:
            kafka_message({'xrf': 'plot', 'uid': uid, 'add': add, 'only': only})
        else:
            dcm, BMMuser = user_ns['dcm'], user_ns['BMMuser']
            plt.clf()
            plt.xlabel('Energy  (eV)')
            plt.ylabel('counts')
            plt.grid(which='major', axis='both')
            plt.xlim(2500, round(dcm.energy.position, -2)+500)
            plt.title('XRF Spectrum')
            s1 = self.channel08.mca.array_data.get()
            e = numpy.arange(0, len(s1)) * 10
            plt.ion()
            plt.plot(e, s1, label='channel 8')
            z = Z_number(BMMuser.element)
            if BMMuser.edge.lower() == 'k':
                label = f'{BMMuser.element} Kα1'
                plt.axvline(x = xraylib.LineEnergy(z, xraylib.KL3_LINE)*1000,  color = 'brown', linewidth=1, label=label)
            elif BMMuser.edge.lower() == 'l3':
                label = f'{BMMuser.element} Lα1'
                plt.axvline(x = xraylib.LineEnergy(z, xraylib.L3M5_LINE)*1000, color = 'brown', linewidth=1, label=label)
            elif BMMuser.edge.lower() == 'l2':
                label = f'{BMMuser.element} Kβ1'
                plt.axvline(x = xraylib.LineEnergy(z, xraylib.L2M4_LINE)*1000, color = 'brown', linewidth=1, label=label)
            elif BMMuser.edge.lower() == 'l1':
                label = f'{BMMuser.element} Kβ3'
                plt.axvline(x = xraylib.LineEnergy(z, xraylib.L1M3_LINE)*1000, color = 'brown', linewidth=1, label=label)
            plt.legend()
            #plt.show()

    def table(self):
        '''Pretty print a table of values for each ROI.
        '''
        BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
        edge = xraylib.EdgeEnergy(Z_number(BMMuser.element), int(edge_number(BMMuser.edge)))*1000
        if dcm.energy.position > edge:
            print(f'{BMMuser.element} {BMMuser.edge} -- current energy: {round(dcm.energy.position, 1)}\n')
        else:
            print(warning_msg(f'{BMMuser.element} {BMMuser.edge} -- current energy: {round(dcm.energy.position, 1)}  *** Below Edge! ***\n'))
        print(' ROI    Chan8 ')
        print('================')
        first_channel_number = self.channel_numbers[0]
        first_channel = self.get_channel(channel_number=first_channel_number)
        for r in first_channel.mcaroi_numbers:
            el = self.channel08.get_mcaroi(mcaroi_number=r).name
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


if sys.version_info[1] == 9:
    BMMXspress3Detector_1Element = build_detector_class(
        channel_numbers=(8,),
        mcaroi_numbers=range(1, 17),
        detector_parent_classes=(BMMXspress3Detector_1Element_Base, )
    )
else:
    BMMXspress3Detector_1Element = build_xspress3_class(
        channel_numbers=(8,),
        mcaroi_numbers=range(1, 17),
        image_data_key="xrf",
        xspress3_parent_classes=(BMMXspress3Detector_1Element_Base, )
    )
        
