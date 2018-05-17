
from ophyd import QuadEM, Component as Cpt, EpicsSignalWithRBV, Signal
import datetime

bmm_metadata_stub = {'Beamline,name': 'BMM (06BM)',
                     'Beamline,collimation': 'paraboloid mirror, 5 nm Rh on 30 nm Pt',
                     'Facility,name': 'NSLS-II',
                     'Facility,energy': '3 GeV',
                     'Beamline,xray_source': 'NSLS-II three-pole wiggler',
                     'Column,01': 'energy eV',
                     'Column,02': 'encoder counts',
                     'Column,03': 'i0 nA',
                     'Column,04': 'it nA',
                     'Column,05': 'ir nA'
                     }


class Ring(Device):
        current  = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}I:Real-I')
        lifetime = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}Lifetime-I')
        mode     = Cpt(EpicsSignal, '-OPS{}Mode-Sts', string=True)

ring = Ring('SR', name='ring')

def bmm_metadata(mode        = 'transmission',
                 edge        = 'K',
                 element     = 'Fe',
                 edge_energy = '7112',
                 focus       = False,
                 hr          = True,
                 direction   = 1,
                 scan        = 'step',
                 channelcut  = True,
                 mono        = 'Si(111)',
                 i0_gas      = 'N2',
                 it_gas      = 'N2',
                 sample      = 'Fe foil',
                 prep        = '',
                 stoichiometry = None
             ):
    '''
    fill a dictionary with BMM-specific metadata.  this will be stored in the <db>.start['md'] field

    Argument list:
      mode          -- 'transmission' or 'fluorescence'
      edge          -- 'K', 'L3', 'L2', or 'L1'
      element       -- one or two letter element symbol
      edge_energy   -- edge energy used to constructing scan parameters
      focus         -- True/False, True for PDS modes A, B, C
      hr            -- True/False, True for PDS modes D, E, F
      direction     -- 1/-1, 1 for increasing, -1 for decreasing
      scan          -- 'step' or 'slew'
      channelcut    -- True/False, False for fixed exit, True for pseudo-channel-cut
      mono          -- 'Si(111)' or 'Si(311)'
      i0_gas        -- a string using N2, He, Ar, and Kr
      it_gas        -- a string using N2, He, Ar, and Kr
      sample        -- one-line sample description
      prep          -- one-line explanation of sample preparation
      stoichiometry -- None or IUCr stoichiometry string
    '''
    
    md                     = bmm_metadata_stub
    md['Facility,current'] = str(ring.current.value) + ' mA'
    md['Facility,mode']    = ring.mode.value
    md['Element,edge']     = edge.capitalize()
    md['Element,symbol']   = element.capitalize()
    md['Scan,edge_energy'] = edge_energy
    md['Mono,name']        = mono
    md['Detector,I0']      = '10 cm ' + i0_gas
    md['Detector,It']      = '25 cm ' + it_gas
    md['Sample,name']      = sample
    md['Sample,prep']      = prep
    if stoichiometry is not None:
        md['Sample,stoichiometry'] = stoichiometry

    if focus:
        md['Beamline,focusing'] = 'torroidal mirror with bender, 5 nm Rh on 30 nm Pt'
    else:
        md['Beamline,focusing'] = 'none'

    if hr:
        md['Beamline,harmonic_rejection'] = 'Pt stripe; Si stripe below 8 keV'
    else:
        md['Beamline,harmonic_rejection'] = 'none'

    if direction > 0:
        md['Mono,direction'] =  'increasing in energy'
    else:
        md['Mono,direction'] =  'decreasing in energy'

    if 'step' in scan:
        md['Mono,scan_type'] = 'step'
    else:
        md['Mono,scan_type'] = 'slew'

    if channelcut is True:
        md['Mono,scan_mode'] = 'pseudo channel cut'
    else:
        md['Mono,scan_mode'] = 'fixed exit'
        
    if 'fluo' in mode:
        md['Column.06'] = 'roi1 counts'
        md['Column,07'] = 'icr1 counts'
        md['Column,08'] = 'ocr1 counts'
        md['Column,09'] = 'corr1 dead-time corrected counts'
        md['Column,10'] = 'roi2 counts'
        md['Column,11'] = 'icr2 counts'
        md['Column,12'] = 'ocr2 counts'
        md['Column,13'] = 'corr2 dead-time corrected counts'
        md['Column,14'] = 'roi3 counts'
        md['Column,15'] = 'icr3 counts'
        md['Column,16'] = 'ocr3 counts'
        md['Column,17'] = 'corr3 dead-time corrected counts'
        md['Column,18'] = 'roi4 counts'
        md['Column,19'] = 'icr4 counts'
        md['Column,20'] = 'ocr4 counts'
        md['Column,21'] = 'corr4 dead-time corrected counts'


    ## set Scan.start_time & Scan.end_time
    # d=datetime.datetime.fromtimestamp(round(header.start['time']))
    # md['Scan,start_time'] = datetime.datetime.isoformat(d)
    # d=datetime.datetime.fromtimestamp(round(header.stop['time']))
    # md['Scan,end_time']   = datetime.datetime.isoformat(d)
    
    return md
