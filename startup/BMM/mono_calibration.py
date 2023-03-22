
from bluesky.preprocessors import finalize_wrapper
from bluesky.plan_stubs import null, sleep, mv, mvr
import matplotlib.pyplot as plt

import configparser, os
config = configparser.ConfigParser()

import lmfit
from numpy import array, pi, sin, linspace, arange
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

from BMM.dcm_parameters import dcm_parameters
from BMM.edge           import change_edge
from BMM.functions      import HBARC, boxedtext
from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.kafka          import kafka_message
from BMM.logging        import BMM_log_info, BMM_msg_hook, report
#from BMM.purpose        import purpose
from BMM.xafs           import xafs
from BMM.resting_state  import resting_state_plan
from BMM.suspenders     import BMM_clear_to_start
from BMM.derivedplot    import close_all_plots, close_last_plot, interpret_click


from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


##  Kraft et al, Review of Scientific Instruments 67, 681 (1996)
##  https://doi.org/10.1063/1.1146657

def calibrate_low_end(mono='111', focus=False):
    '''Step through the lower 5 elements of the mono calibration procedure.'''
    BMMuser, shb, dcm_pitch = user_ns['BMMuser'], user_ns['shb'], user_ns['dcm_pitch']
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting macro....\n'))
        return(yield from null())
    
    BMM_log_info('Beginning low end calibration macro')
    def main_plan(focus):
        BMMuser.prompt = False

        datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
        handle = open(datafile, 'w')
        handle.write('[config]\n')
        handle.write("mono      = %s\n" % mono)
        if mono == '111':
            handle.write('DSPACING  = 3.13597211\n')
        else:
            handle.write('DSPACING  = 1.63762644\n')
        handle.write('thistitle = Si(%s) calibration curve\n' % mono)
        handle.write('reference = Kraft et al, Review of Scientific Instruments 67, 681 (1996)\n')
        handle.write('doi       = https://doi.org/10.1063/1.1146657\n\n')
        handle.write('##       found, tabulated, found_angle, dcm_pitch\n')
        handle.write('[edges]\n')
        handle.flush()

    
        yield from change_edge('Fe', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='fecal', element='Fe', sample='Fe foil')
        close_last_plot()
        handle.write('fe = 11111.11,    7110.75,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Co', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='cocal', element='Co', sample='Co foil')
        close_last_plot()
        handle.write('co = 11111.11,    7708.78,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Ni', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='nical', element='Ni', sample='Ni foil')
        close_last_plot()
        handle.write('ni = 11111.11,    8331.49,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Cu', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='cucal', element='Cu', sample='Cu foil')
        close_last_plot()
        handle.write('cu = 11111.11,    8980.48,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Zn', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='zncal', element='Zn', sample='Zn foil')
        close_last_plot()
        handle.write('zn = 11111.11,    9660.76,    22222.22,   %.5f\n' % pitch)

        handle.flush()
        handle.close()

        #yield from shb.close_plan()

    def cleanup_plan():
        yield from resting_state_plan()
    yield from finalize_wrapper(main_plan(focus), cleanup_plan())    
    yield from resting_state_plan()
    BMM_log_info('Low end calibration macro finished!')


def calibrate_high_end(mono='111', focus=False):
    '''Step through the upper 5 elements of the mono calibration procedure.'''
    BMMuser, shb, dcm_pitch = user_ns['BMMuser'], user_ns['shb'], user_ns['dcm_pitch']
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting macro....\n'))
        return(yield from null())
    
    BMM_log_info('Beginning high end calibration macro')
    def main_plan(focus):
        BMMuser.prompt = False
        datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
        handle = open(datafile, 'a')
    
        #yield from shb.open_plan()

        yield from change_edge('Pt', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='ptcal', element='Pt', edge='L3', sample='Pt foil')
        close_last_plot()
        handle.write('pt = 11111.11,    11562.76,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Au', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='aucal', element='Au', edge='L3', sample='Au foil')
        close_last_plot()
        handle.write('au = 11111.11,    11919.70,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Pb', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='pbcal', element='Pb', edge='L3', sample='Pb foil')
        close_last_plot()
        handle.write('pb = 11111.11,    13035.07,    22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Nb', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='nbcal', element='Nb', sample='Nb foil')
        close_last_plot()
        handle.write('nb = 11111.11,     18982.97,   22222.22,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Mo', target=0, focus=focus)
        pitch = dcm_pitch.user_readback.get()
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='mocal', element='Mo', sample='Mo foil')
        close_last_plot()
        handle.write('mo = 11111.11,    20000.36,    22222.22,   %.5f\n' % pitch)

        handle.flush()
        handle.close()

        #yield from shb.close_plan()

    def cleanup_plan():
        yield from resting_state_plan()
    yield from finalize_wrapper(main_plan(focus), cleanup_plan())    
    yield from resting_state_plan()
    BMM_log_info('High end calibration macro finished!')


## there is a historical reason this is split into two halves -- the original reference holder had 5 slots
def calibrate(focus=False):
    "Run a sequence of 10 foil XANES scans, Fe to Mo, to calibrate the DCM."
    def main_plan():
        dcm, BMMuser = user_ns['dcm'], user_ns['BMMuser']
        BMMuser.instrument = ''
        report(f'Calibrating the {dcm._crystal} monochrmoator', 'bold')
        yield from calibrate_low_end(mono=dcm._crystal, focus=focus)
        yield from calibrate_high_end(mono=dcm._crystal, focus=focus)
        yield from resting_state_plan()
    def cleanup_plan():
        yield from resting_state_plan()
    yield from finalize_wrapper(main_plan(), cleanup_plan())    


def calibrate_pitch(mono='111'):
    BMMuser = user_ns['BMMuser']
    # read content from INI file
    datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
    print(f'reading {datafile}')
    config.read_file(open(datafile))

    edges = dict()
    for i in config.items('edges'):
        el   = i[0]
        vals = [float(j) for j in i[1].split(',')] # convert CSV string -> list of strings -> list of floats
        edges[el] = vals


    
    # organize the data from the INI file
    ordered = [y[1] for y in sorted([(edges[x][1], x) for x in edges.keys()])]
    ee = list()
    tt = list()
    for el in ordered:
        ee.append(edges[el][1])
        tt.append(edges[el][3])
        
    mod    = lmfit.LinearModel()
    pars   = mod.guess(tt, x=ee)
    out    = mod.fit(tt, pars, x=ee)
    print(whisper(out.fit_report(min_correl=0)))
    out.plot()

    
def calibrate_mono(mono='111'):
    BMMuser, shb, dcm, dcm_pitch = user_ns['BMMuser'], user_ns['shb'], user_ns['dcm'], user_ns['dcm_pitch']
    BMM_dcm = dcm_parameters()

    # read content from INI file
    datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
    print(f'reading {datafile}')
    config.read_file(open(datafile))
    DSPACING  = float(config.get('config', 'DSPACING'))
    thistitle = 'Si(%s) calibration curve' % mono

    edges = dict()
    for i in config.items('edges'):
        el   = i[0]
        vals = [float(j) for j in i[1].split(',')] # convert CSV string -> list of strings -> list of floats
        edges[el] = vals

    # organize the data from the INI file
    ordered = [y[1] for y in sorted([(edges[x][1], x) for x in edges.keys()])]
    
    tabulated = list()
    ee = list()
    tt = list()
    for el in ordered:
        ee.append(edges[el][1])
        tt.append(edges[el][2])

    # working arrays
    e      = array(ee)
    th     = array(tt)
    energy = e.copy(),
    theta  = th.copy()

    # limfit parameters
    params = lmfit.Parameters()
    params.add('d',      value=DSPACING, vary=True)
    params.add('offset', value=0,        vary=True)
    

    def match(pars, x, data=None):
        vals      = pars.valuesdict()
        d_spacing = vals['d']
        offset    = vals['offset']
        model     = (2*pi*HBARC) / ( 2 * d_spacing * sin((x+offset)*pi/180) ) # HBARC defined in 20-dcm.py
        func      = model - data
        if data is None:
            return model
        return func

    
    fit = lmfit.minimize(match, params, args=(th,), kws={'data': e})
    boxedtext('fit results', lmfit.fit_report(fit), 'green')

    d_spacing = fit.params.get('d').value
    derr =  fit.params.get('d').stderr
    offset = fit.params.get('offset').value
    oerr = fit.params.get('offset').stderr
    energy = (2*pi*HBARC) / (2*d_spacing*sin((theta+offset)*pi/180))

    i = 0
    text  = '\n #  El.  tabulated    found        diff\n'
    found = list()
    for el in ordered:
        val = (2*pi*HBARC) / (2*d_spacing*sin((tt[i]+offset)*pi/180))
        found.append(val)
        text = text + "    %-2s  %9.3f  %9.3f  %9.3f\n" % (el.capitalize(), ee[i], found[i], found[i]-ee[i])
        i = i+1
    boxedtext('comparison with tabulated values', text, 'lightgray')
    text = ' self.dspacing_%s = %.7f\n' % (dcm._crystal, d_spacing)
    if dcm._crystal == '111':
        text += ' self.offset_111 = %.7f' % (BMM_dcm.offset_111 + offset)
        boxedtext('new values for 19-dcm-parameters.py', text, 'lightgray')
    else:
        text += ' self.offset_311 = %.7f' % (BMM_dcm.offset_311 + offset)
        boxedtext('new values for BMM/dcm-parameters.py', text, 'lightgray')

    ## plot with the kafka consumer
    kafka_message({'mono_calibration' : True,
                   'found'    : found,
                   'ee'       : ee,
                   'tt'       : tt,
                   'mono'     : mono,
                   'dspacing' : (d_spacing, derr),
                   'offset'   : (offset, oerr), })

