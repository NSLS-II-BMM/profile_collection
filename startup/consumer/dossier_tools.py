import numpy
from BMM.periodictable import edge_energy


def xrf_metadata(catalog, uid):
    record = catalog[uid]
    el = record.metadata['start']['XDI']['Element']['symbol']
    (roi1, roi2, roi3, roi4) = (float(record.primary.read()[f'{el}1']),
                                float(record.primary.read()[f'{el}2']),
                                float(record.primary.read()[f'{el}3']),
                                float(record.primary.read()[f'{el}4']) )
    roistring = f'{roi1}, {roi2}, {roi3}, {roi4}'
    (ocr1, ocr2, ocr3, ocr4) = (numpy.array(record.primary.read()['4-element SDD_channel01']).sum(),
                                numpy.array(record.primary.read()['4-element SDD_channel02']).sum(),
                                numpy.array(record.primary.read()['4-element SDD_channel03']).sum(),
                                numpy.array(record.primary.read()['4-element SDD_channel04']).sum() )
    ocrstring = f'{ocr1}, {ocr2}, {ocr3}, {ocr4}'

    try:
        pccenergy = record['start']['XDI']['_pccenergy']
    except:
        ed = record.metadata['start']['XDI']['Element']['edge']
        pccenergy = edge_energy(el, ed) + 300


    return({'symbol': el, 'rois': roistring, 'ocrs': ocrstring, 'pccenergy': pccenergy,})
                                
def current_slot(value=None, which='wheel'):
    '''Return the slot number for a sample wheel for a value of xafs_wheel.'''
    if which == 'wheel':
        zero = -30
    else:
        zero = 0
    if value is not None:
        angle = round(value)
    else:
        return 0
    this = round((-1*zero-15+angle) / (-15)) % 24
    if this == 0: this = 24
    return this

def current_spinner(value=None):
    '''Return the spinner number as an integer for a value of xafs_garot'''
    if value is None:
        return 1
    cur = value % 360
    here = (9-round(cur/45)) % 8
    if here == 0:
        here = 8
    return here

def motor_sidebar(catalog, uid):
    '''Generate a list of motor positions to be used in the static html page for a scan sequence.
    Return value is a long string with html tags and entities embedded in the string.

    Parameters:
    ===========
    catalog: a Tiled catalog
    uid: UID string for the record

    The Tiled catalog is, presumably, obtained like this:
       from tiled.client import from_profile
       catalog = from_profile('bmm')

    '''
    baseline = catalog[uid].baseline.read()
    motors = ''
    try:
        pccenergy = catalog[uid].metadata['start']['XDI']['_pccenergy']
    except:
        el = catalog[uid].metadata['start']['XDI']['Element']['symbol']
        ed = catalog[uid].metadata['start']['XDI']['Element']['edge']
        pccenergy = edge_energy(el, ed) + 300
    
    def val(motor):
        try:
            value = float(baseline[motor][0])
        except:
            value = 0
        return(value)

    mono = get_mono(catalog[uid], val('dcm_x'))
    (bragg, para, perp) = dcm_positions(pccenergy, mono)


    
    mlist = []
    mlist.append('XAFS stages:')
    mlist.append(f'xafs_x, {val("xafs_x"):.3f}, xafs_y, {val("xafs_y"):3f}')
    mlist.append(f'xafs_pitch, {val("xafs_pitch"):.3f}, xafs_roll, {val("xafs_roll"):.3f}')
    mlist.append(f'xafs_ref, {val("xafs_ref"):.3f}, xafs_wheel, {val("xafs_wheel"):.3f}')
    mlist.append(f'xafs_refx, {val("xafs_refx"):.3f}, xafs_refy, {val("xafs_refy"):.3f}')
    mlist.append(f'xafs_garot, {val("xafs_garot"):.3f}, xafs_det, {val("xafs_det"):3f}')
    mlist.append(f'wheel slot = {current_slot(val("xafs_wheel"), "wheel"):2d}')
    mlist.append(f'glancing angle spinner = {current_spinner(val("xafs_garot")):2d}')
    mlist.append(f'dm3_bct: {val("dm3_bct"):.3f}')
        
    motors += '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('Slits3:')
    mlist.append(f'slits3.vsize, {val("slits3_vsize"):.3f}, slits3.vcenter, {val("slits3_vcenter"):.3f}')
    mlist.append(f'slits3.hsize, {val("slits3_hsize"):.3f}, slits3.hcenter, {val("slits3_hcenter"):.3f}')
    mlist.append(f'slits3.top, {val("slits3_top"):.3f}, slits3.bottom, {val("slits3_bottom"):.3f}')
    mlist.append(f'slits3.outboard, {val("slits3_outboard"):.3f}, slits3.inboard, {val("slits3_inboard"):.3f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('M2')
    mlist.append(f'm2.vertical, {val("m2_vertical"):.3f}, m2.yu, {val("m2_yu"):.3f}')
    mlist.append(f'm2.lateral, {val("m2_latral"):.3f}, m2.ydo, {val("m2_ydo"):.3f}')
    mlist.append(f'm2.pitch, {val("m2_pitch"):.3f}, m2.ydi, {val("m2_ydi"):.3f}')
    mlist.append(f'm2.roll, {val("m2_roll"):.3f}, m2.xu, {val("m2_xu"):.3f}')
    mlist.append(f'm2.yaw, {val("m2_yaw"):.3f}, m2.xd, {val("m2_xd"):.3f}')
    mlist.append(f'm2.bender, {val("m2_bender"):.1f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    stripe = '(Rh/Pt stripe)'
    if val("m3_xu") < 0:
        stripe = '(Si stripe)'
    mlist.append('M3  %s' % stripe)
    mlist.append(f'm3.vertical, {val("m3_vertical"):.3f}, m3.yu, {val("m3_yu"):.3f}')
    mlist.append(f'm3.lateral, {val("m3_latral"):.3f}, m3.ydo, {val("m3_ydo"):.3f}')
    mlist.append(f'm3.pitch, {val("m3_pitch"):.3f}, m3.ydi, {val("m3_ydi"):.3f}')
    mlist.append(f'm3.roll, {val("m3_roll"):.3f}, m3.xu, {val("m3_xu"):.3f}')
    mlist.append(f'm3.yaw, {val("m3_yaw"):.3f}, m3.xd, {val("m3_xd"):.3f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('XAFS table:')
    mlist.append(f'xt.vertical, {val("xafs_table_vertical"):.3f}, xt.yu, {val("xafs_table_yu"):.3f}')
    mlist.append(f'xt.pitch, {val("xafs_table_pitch"):.3f}, xt.ydo, {val("xafs_table_ydo"):.3f}')
    mlist.append(f'xt.roll, {val("xafs_table_roll"):.3f}, xt.ydi, {val("xafs_table_ydi"):.3f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('Slits2:')
    mlist.append(f'slits2.vsize, {val("slits2_vsize"):.3f}, slits2.vcenter, {val("slits2_vcenter"):.3f}')
    mlist.append(f'slits2.hsize, {val("slits2_hsize"):.3f}, slits2.hcenter, {val("slits2_hcenter"):.3f}')
    mlist.append(f'slits2.top, {val("slits2_top"):.3f}, slits2.bottom, {val("slits2_bottom"):.3f}')
    mlist.append(f'slits2.outboard, {val("slits2_outboard"):.3f}, slits2.inboard, {val("slits2_inboard"):.3f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append(f'DCM (at {pccenergy:.1f}):')
    mlist.append(f'dcm_bragg, {bragg:.3f}, dcm_para, {para:.3f}')
    mlist.append(f'dcm_perp, {perp:.3f}, dcm_pitch, {val("dcm_pitch"):.3f}')
    mlist.append(f'dcm_roll, {val("dcm_roll"):.3f}, dcm_x, {val("dcm_x"):.3f}')
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    
    motors += f'\n<br><br>dm3_foils, {val("dm3_foils"):.3f}'
    motors += f'\n<br>dm2_fs, {val("dm2_fs"):.3f}'

    return motors


HBARC = 1973.27053324
SI111 = 6.2710834
SI311 = 3.2753182
def e2a(energy, mono='111'):
    """convert absolute energy to monochromator angle"""
    TWOD = SI111
    if mono == '311':
        TWOD = SI311
    wavelength = 2*numpy.pi*HBARC / energy
    angle = 180 * numpy.arcsin(wavelength / TWOD) / numpy.pi
    return angle

def dcm_positions(energy, mono='Si(111)'):
    OFFSET = 30
    TWOD = SI111
    if mono == 'Si(311)':
        TWOD = SI311
    elif mono == 'Si(333)':
        TWOD = SI111/3
    wavelength = 2*numpy.pi*HBARC / energy
    angle = numpy.arcsin(wavelength / TWOD)
    bragg = 180 * numpy.arcsin(wavelength/TWOD) / numpy.pi
    para  = OFFSET / (2*numpy.sin(angle))
    perp  = OFFSET / (2*numpy.cos(angle))
    return(bragg, para, perp)

def get_mono(record, val):
    if val > 10:
        mono = 'Si(311)'
    else:
        ## need to determine if Si(333) is being used
        el = record.metadata['start']['XDI']['Element']['symbol']
        ed = record.metadata['start']['XDI']['Element']['edge']
        try:
            pccen = record.metadata['start']['XDI']['_pccenergy']
        except:
            pccen = edge_energy(el, ed) + 300
        if pccen < edge_energy(el, ed) - 500:
            mono = 'Si(333)'
        else:
            mono = 'Si(111)'
    


def describe_mode(catalog, uid):
    '''Determine photon delivery mode from the contents of the baseline
    of a specified record.

    Parameters:
    ===========
    catalog: a Tiled catalog
    uid: UID string for the record

    The Tiled catalog is, presumably, obtained like this:
       from tiled.client import from_profile
       catalog = from_profile('bmm')

    '''
    record = catalog[uid]
    baseline = record.baseline.read()
    def val(motor):
        try:
            value = float(baseline[motor][0])
        except:
            value = 0
        return(value)
    if val('m2_vertical') < 0: # this is a focused mode
        if val('m2_pitch') > 3:
            mode, desc = 'XRD', 'focused at goniometer, >8 keV'
        else:
            if val('m3_vertical') > -2:
                mode, desc = 'A',  'focused, >8 keV'
            elif val('m3_vertical') > -7:
                mode, desc = 'B',  'focused, <6 keV'
            else:
                mode, desc = 'C',  'focused, 6 to 8 keV'
    else:
        if val('m3_pitch') < 3:
            mode, desc = 'F',  'unfocused, <6 keV'
        elif val('m3.lateral') > 0:
            mode, desc = 'D',  'unfocused, >8 keV'
        else:
            mode, desc = 'E',  'unfocused, 6 to 8 keV'

    mono = get_mono(record, val('dcm_x'))
        
    return({'mode': mode, 'mode_description': desc, 'mono': mono})
