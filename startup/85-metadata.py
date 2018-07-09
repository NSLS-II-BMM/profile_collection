
from ophyd import QuadEM, Component as Cpt, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV, Signal
import datetime

bmm_metadata_stub = {'XDI,Beamline,name': 'BMM (06BM) -- Beamline for Materials Measurement',
                     'XDI,Beamline,collimation': 'paraboloid mirror, 5 nm Rh on 30 nm Pt',
                     'XDI,Facility,name': 'NSLS-II',
                     'XDI,Facility,energy': '3 GeV',
                     'XDI,Beamline,xray_source': 'NSLS-II three-pole wiggler',
                     'XDI,Column,01': 'energy eV',
                     'XDI,Column,02': 'encoder counts',
                     'XDI,Column,03': 'i0 nA',
                     'XDI,Column,04': 'it nA',
                     'XDI,Column,05': 'ir nA'
                     }


class TC(Device):
    temperature = Cpt(EpicsSignal, 'T-I-I')

first_crystal = TC('XF:06BMA-OP{Mono:DCM-Crys:1}', name='first_crystal')
compton_shield = TC('XF:06BMA-OP{Mono:DCM-Crys:1-Ax:R}', name='compton_shield')


class Ring(Device):
        current    = Cpt(EpicsSignalRO, ':OPS-BI{DCCT:1}I:Real-I')
        lifetime   = Cpt(EpicsSignalRO, ':OPS-BI{DCCT:1}Lifetime-I')
        energy     = Cpt(EpicsSignalRO, '{}Energy_SRBend')
        mode       = Cpt(EpicsSignalRO, '-OPS{}Mode-Sts', string=True)
        filltarget = Cpt(EpicsSignalRO, '-HLA{}FillPattern:DesireImA')

ring = Ring('SR', name='ring')

def bmm_metadata(measurement = 'transmission',
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
                 ir_gas      = 'N2',
                 sample      = 'Fe foil',
                 prep        = '',
                 stoichiometry = None,
                 mode        = 'transmission',
                 comment     = ''
                ):
    '''
    fill a dictionary with BMM-specific metadata.  this will be stored in the <db>.start['md'] field

    Argument list:
      measurement   -- 'transmission' or 'fluorescence'
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
      mode          -- transmission, fluorescence, reference
      comment       -- user-supplied, free-form comment string
    '''

    md                          = bmm_metadata_stub
    md['XDI,_mode']             = mode,
    md['XDI,_comment']          = comment,
    md['XDI,_scantype']         = 'xafs step scan',
    md['XDI,Element,edge']      = edge.capitalize()
    md['XDI,Element,symbol']    = element.capitalize()
    md['XDI,Scan,edge_energy']  = edge_energy
    md['XDI,Mono,name']         = mono
    md['XDI,Mono,encoder_resolution']  = dcm.bragg.resolution.value
    md['XDI,Mono,angle_offset'] = dcm.bragg.user_offset.value
    md['XDI,Detector,I0']       = '10 cm ' + i0_gas
    md['XDI,Detector,It']       = '25 cm ' + it_gas
    md['XDI,Detector,Ir']       = '25 cm ' + ir_gas
    md['XDI,Sample,name']       = sample
    md['XDI,Sample,prep']       = prep
    md['XDI,Sample,x_position'] = xafs_linx.user_readback.value
    md['XDI,Sample,y_position'] = xafs_liny.user_readback.value
    ## what about roll, pitch, rotX ???
    if stoichiometry is not None:
        md['XDI,Sample,stoichiometry'] = stoichiometry

    if focus:
        md['XDI,Beamline,focusing'] = 'torroidal mirror with bender, 5 nm Rh on 30 nm Pt'
    else:
        md['XDI,Beamline,focusing'] = 'none'

    if hr:
        md['XDI,Beamline,harmonic_rejection'] = 'Pt stripe; Si stripe below 8 keV'
    else:
        md['XDI,Beamline,harmonic_rejection'] = 'none'

    if direction > 0:
        md['XDI,Mono,direction'] =  'increasing in energy'
    else:
        md['XDI,Mono,direction'] =  'decreasing in energy'

    if 'step' in scan:
        md['XDI,Mono,scan_type'] = 'step'
    else:
        md['XDI,Mono,scan_type'] = 'slew'

    if channelcut is True:
        md['XDI,Mono,scan_mode'] = 'pseudo channel cut'
    else:
        md['XDI,Mono,scan_mode'] = 'fixed exit'

    if 'fluo' in measurement:
        md['XDI,Detector,fluorescence'] = 'SII Vortex ME4 (4-element silicon drift)'

    # if 'fluo' in measurement:
    #     md['XDI,Column,06'] = 'roi1 counts'
    #     md['XDI,Column,07'] = 'icr1 counts'
    #     md['XDI,Column,08'] = 'ocr1 counts'
    #     md['XDI,Column,09'] = 'corr1 dead-time corrected counts'
    #     md['XDI,Column,10'] = 'roi2 counts'
    #     md['XDI,Column,11'] = 'icr2 counts'
    #     md['XDI,Column,12'] = 'ocr2 counts'
    #     md['XDI,Column,13'] = 'corr2 dead-time corrected counts'
    #     md['XDI,Column,14'] = 'roi3 counts'
    #     md['XDI,Column,15'] = 'icr3 counts'
    #     md['XDI,Column,16'] = 'ocr3 counts'
    #     md['XDI,Column,17'] = 'corr3 dead-time corrected counts'
    #     md['XDI,Column,18'] = 'roi4 counts'
    #     md['XDI,Column,19'] = 'icr4 counts'
    #     md['XDI,Column,20'] = 'ocr4 counts'
    #     md['XDI,Column,21'] = 'corr4 dead-time corrected counts'


    return md
