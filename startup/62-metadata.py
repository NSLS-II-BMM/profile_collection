
from ophyd import QuadEM, Component as Cpt, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV, Signal
import datetime
import copy

run_report(__file__)



class TC(Device):
    temperature = Cpt(EpicsSignal, 'T-I-I')

first_crystal  = TC('XF:06BMA-OP{Mono:DCM-Crys:1}',      name='first_crystal')
compton_shield = TC('XF:06BMA-OP{Mono:DCM-Crys:1-Ax:R}', name='compton_shield')


class Ring(Device):
        current    = Cpt(EpicsSignalRO, ':OPS-BI{DCCT:1}I:Real-I')
        lifetime   = Cpt(EpicsSignalRO, ':OPS-BI{DCCT:1}Lifetime-I')
        energy     = Cpt(EpicsSignalRO, '{}Energy_SRBend')
        mode       = Cpt(EpicsSignalRO, '-OPS{}Mode-Sts', string=True)
        filltarget = Cpt(EpicsSignalRO, '-HLA{}FillPattern:DesireImA')

ring = Ring('SR', name='ring')

## some heuristics for determining state of M2 and M3
def mirror_state():
    if m2.vertical.readback.value > 0:
        m2state = 'not in use'
    else:
        m2state = 'torroidal mirror, 5 nm Rh on 30 nm Pt, pitch = %.2f mrad, bender = %d counts' % (7.0 - m2.pitch.readback.value,
                                                                                                    int(m2_bender.user_readback.value))
    if m3.lateral.readback.value > 0:
        stripe =  'Pt stripe'
    else:
        stripe =  'Si stripe'
    if abs(m3.vertical.readback.value + 1.5) < 0.1:
        m3state = 'not in use'
    else:
        m3state = 'flat mirror, %s, pitch = %.1f mrad relative to beam' % (stripe, 7.0 - m2.pitch.readback.value)
    return(m2state, m3state)



bmm_metadata_stub = {'Beamline': {'name'        : 'BMM (06BM) -- Beamline for Materials Measurement',
                                  'collimation' : 'paraboloid mirror, 5 nm Rh on 30 nm Pt',
                                  'xray_source' : 'NSLS-II three-pole wiggler',
                              },
                     'Facility': {'name'        : 'NSLS-II',
                                  'energy'      : '3 GeV',},
                     
                     'Column':   {'01'          : 'energy eV',
                                  '02'          : 'requested energy eV',
                                  '03'          : 'measurement time sec',
                                  '04'          : 'mu(E)',
                                  '05'          : 'i0 nA',
                                  '06'          : 'it nA',
                                  '07'          : 'ir nA'},
                 }


def bmm_metadata(measurement   = 'transmission',
                 experimenters = '',
                 edge          = 'K',
                 element       = 'Fe',
                 edge_energy   = '7112',
                 direction     = 1,
                 scantype      = 'step',
                 channelcut    = True,
                 mono          = 'Si(111)',
                 i0_gas        = 'N2',
                 it_gas        = 'N2',
                 ir_gas        = 'N2',
                 sample        = 'Fe foil',
                 prep          = '',
                 stoichiometry = None,
                 mode          = 'transmission',
                 comment       = '',
                 ththth        = False,):
    '''
    fill a dictionary with BMM-specific metadata.  this will be stored in the <db>.start['md'] field

    Argument list:
      measurement   -- 'transmission' or 'fluorescence'
      edge          -- 'K', 'L3', 'L2', or 'L1'
      element       -- one or two letter element symbol
      edge_energy   -- edge energy used to constructing scan parameters
      direction     -- 1/0/-1, 1 for increasing, -1 for decreasing, 0 for fixed energy
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
      ththth        -- True is measuring with the Si(333) relfection
    '''

    md                         = copy.deepcopy(bmm_metadata_stub)
    md['_mode']                = mode,
    #md['_kind']                = kind,
    md['_comment']             = comment,
    #md['_scantype']            = 'xafs step scan'
    if 'fixed' in scantype:
        md['_scantype']        = 'single-energy x-ray absorption detection'
    for k in ('Beamline', 'Element', 'Scan', 'Mono', 'Detector', 'Facility', 'Sample', 'Column'):
        if k not in md:
            md[k] = dict()
    md['Element']['edge']            = edge.capitalize()
    md['Element']['symbol']          = element.capitalize()
    md['Scan']['edge_energy']        = edge_energy
    md['Scan']['experimenters']      = experimenters
    md['Mono']['name']               = 'Si(%s)' % dcm._crystal
    md['Mono']['d_spacing']          = '%.7f Å' % (dcm._twod/2)
    md['Mono']['encoder_resolution'] = dcm.bragg.resolution.value
    md['Mono']['angle_offset']       = dcm.bragg.user_offset.value
    md['Detector']['I0']             = '10 cm ' + i0_gas
    md['Detector']['It']             = '25 cm ' + it_gas
    md['Detector']['Ir']             = '25 cm ' + ir_gas
    md['Facility']['GUP']            = BMMuser.gup
    md['Facility']['SAF']            = BMMuser.saf
    md['Sample']['name']             = sample
    md['Sample']['prep']             = prep
    #md['XDI']['Sample']['x_position']       = xafs_linx.user_readback.value
    #md['XDI']['Sample']['y_position']       = xafs_liny.user_readback.value
    #md['XDI']['Sample']['roll_position']    = xafs_roll.user_readback.value
    ## what about pitch, linxs, rotX ???
    if stoichiometry is not None:
        md['Sample']['stoichiometry'] = stoichiometry

    if ththth:
        md['Mono']['name']            = 'Si(333)'
        md['Mono']['d_spacing']       = '%.7f Å' % (dcm._twod/6)
            
        
    (md['Beamline']['focusing'], md['Beamline']['harmonic_rejection']) = mirror_state()

    if direction > 0:
        md['Mono']['direction'] = 'increasing in energy'
    elif direction == 0:
        md['Mono']['direction'] = 'fixed in energy'
    else:
        md['Mono']['direction'] = 'decreasing in energy'

    if 'step' in scantype:
        md['Mono']['scan_type'] = 'step'
    elif 'fixed' in scantype:
        md['Mono']['scan_type'] = 'single energy'
    else:
        md['Mono']['scan_type'] = 'slew'

    if channelcut is True:
        md['Mono']['scan_mode'] = 'pseudo channel cut'
    else:
        md['Mono']['scan_mode'] = 'fixed exit'

    if 'fluo' in measurement or 'flou' in measurement or 'both' in measurement:
        md['Detector']['fluorescence'] = 'SII Vortex ME4 (4-element silicon drift)'
        md['Detector']['deadtime_correction'] = 'DOI: 10.1107/S0909049510009064'

    if 'yield' in measurement:
        md['Detector']['yield'] = 'simple electron yield detector with batteries and He'

    return md

def metadata_at_this_moment():
    '''Gather the sort of scan metadata that could change between scans
    in a scan sequence.  Return a dictionary.

    '''
    rightnow = dict()
    rightnow['Facility'] = dict()
    #rightnow['Mono']['first_crystal_temperature']  = float(first_crystal.temperature.value)
    #rightnow['Mono']['compton_shield_temperature'] = float(compton_shield.temperature.value)
    #rightnow['Facility']['current']  = str(ring.current.value) + ' mA'
    try:
        rightnow['Facility']['energy']   = str(round(ring.energy.value/1000., 1)) + ' GeV'
        rightnow['Facility']['mode']     = ring.mode.value
    except:
        rightnow['Facility']['energy']   = '0 GeV'
        rightnow['Facility']['mode']     = 'Maintenance'
    if rightnow['Facility']['mode'] == 'Operations':
        rightnow['Facility']['mode'] = 'top-off'
    return rightnow



def display_XDI_metadata(dct):
    for family, ddd in dct.items():
        if type(ddd) is dict:
            for item, value in ddd.items():
                print("\t{:30} {}".format(family+'.'+item+':', value))
