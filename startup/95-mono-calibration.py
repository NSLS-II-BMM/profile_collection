import configparser
config = configparser.ConfigParser()

import lmfit

import pprint
pp = pprint.PrettyPrinter(indent=4)
from numpy import array

import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

##  Kraft et al, Review of Scientific Instruments 67, 681 (1996)
##  https://doi.org/10.1063/1.1146657

def calibrate_low_end(mono='111'):
    '''Step through the lower 5 elements of the mono calibration procedure.'''
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting macro....\n'))
        return(yield from null())
    
    BMM_log_info('Beginning low end calibration macro')
    def main_plan():
        BMMuser.prompt = False

        ### ---------------------------------------------------------------------------------------
        ### BOILERPLATE ABOVE THIS LINE -----------------------------------------------------------
        ##  EDIT BELOW THIS LINE

        foils.set('Fe Co Ni Cu Zn') 
        
        datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
        handle = open(datafile, 'w')
        handle.write('[config]\n')
        handle.write("mono      = '%s'\n" % mono)
        if mono == '111':
            handle.write('DSPACING  = 3.13597211\n')
        else:
            handle.write('DSPACING  = 1.63762644\n')
        handle.write("thistitle = 'Si(%s) calibration curve'\n\n" % mono)
        handle.write('##       found, tabulated, found_angle, dcm_pitch\n')
        handle.write('[edges]\n')
        handle.flush()

    
        yield from change_edge('Fe', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='fecal', edge='Fe', e0=7112, sample='Fe foil')
        close_last_plot()
        handle.write('fe = 12345.12,    7110.75,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Co', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='cocal', edge='Co', e0=7709, sample='Co foil')
        close_last_plot()
        handle.write('co = 12345.12,    7708.78,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Ni', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='nical', edge='Ni', e0=8333, sample='Ni foil')
        close_last_plot()
        handle.write('ni = 12345.12,    8331.49,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Cu', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='cucal', edge='Cu', e0=8979, sample='Cu foil')
        close_last_plot()
        handle.write('cu = 12345.12,    8980.48,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Zn', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='zncal', edge='Zn', e0=9659, sample='Zn foil')
        close_last_plot()
        handle.write('zn = 12345.12,    9660.76,    12.123456,   %.5f\n' % pitch)

        handle.flush()
        handle.close()

        yield from shb.close_plan()
        
        ##  EDIT ABOVE THIS LINE
        ### BOILERPLATE BELOW THIS LINE -----------------------------------------------------------
        ### ---------------------------------------------------------------------------------------

    def cleanup_plan():
        yield from resting_state_plan()
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(), cleanup_plan())    
    yield from resting_state_plan()
    BMM_log_info('Low end calibration macro finished!')


def calibrate_high_end(mono='111'):
    '''Step through the upper 5 elements of the mono calibration procedure.'''
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting macro....\n'))
        return(yield from null())
    
    BMM_log_info('Beginning high end calibration macro')
    def main_plan():
        BMMuser.prompt = False

        ### ---------------------------------------------------------------------------------------
        ### BOILERPLATE ABOVE THIS LINE -----------------------------------------------------------
        ##  EDIT BELOW THIS LINE

        foils.set('Pt Au Pb Nb Mo') 
        
        datafile = os.path.join(BMMuser.DATA, 'edges%s.ini' % mono)
        handle = open(datafile, 'a')
    
        yield from change_edge('Pt', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='ptcal', edge='Pt', e0=11563, sample='Pt foil')
        close_last_plot()
        handle.write('pt = 12345.12,    11562.76,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Au', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='aucal', edge='Au', e0=11919, sample='Au foil')
        close_last_plot()
        handle.write('au = 12345.12,    11919.70,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Pb', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='pbcal', edge='Pb', e0=13035, sample='Pb foil')
        close_last_plot()
        handle.write('pb = 12345.12,    13035.07,    12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Nb', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='nbcal', edge='Nb', e0=18986, sample='Nb foil')
        close_last_plot()
        handle.write('nb = 12345.12,     18982.97,   12.123456,   %.5f\n' % pitch)
        handle.flush()

        yield from change_edge('Mo', target=0)
        pitch = dcm_pitch.user_readback.value
        yield from xafs('/home/xf06bm/Data/Staff/mono_calibration/cal.ini', folder=BMMuser.DATA, filename='mocal', edge='Mo', e0=20000, sample='Mo foil')
        close_last_plot()
        handle.write('mo = 12345.12,    20000.36,    12.123456,   %.5f\n' % pitch)

        handle.flush()
        handle.close()

        yield from shb.close_plan()
        
        ##  EDIT ABOVE THIS LINE
        ### BOILERPLATE BELOW THIS LINE -----------------------------------------------------------
        ### ---------------------------------------------------------------------------------------

    def cleanup_plan():
        yield from resting_state_plan()
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(), cleanup_plan())    
    yield from resting_state_plan()
    BMM_log_info('High end calibration macro finished!')

    

def calibrate_mono(mono='111'):
    # read content from INI file
    if mono == '111':
        config.read_file(open('/home/xf06bm/Data/Staff/mono_calibration/edges111.ini'))
    else:
        config.read_file(open('/home/xf06bm/Data/Staff/mono_calibration/edges311.ini'))
    # mono      = config.get('config', 'mono')
    DSPACING  = float(config.get('config', 'DSPACING'))
    # thistitle = config.get('config', 'thistitle')
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

    y1 = 13.5
    y2 = 12.9
    if mono == '311':
        (y1, y2) = (2*y1, 2*y2)

    ## cubic interpolation of tabulated edge energies ... eye candy
    xnew = np.linspace(min(ee),max(ee),100)
    f = interp1d(ee, tt, kind='cubic')
        
    plt.cla()
    #fig, ax = plt.subplots()
    plt.plot(xnew, f(xnew), label='tabulated')
    plt.plot(found, tt, 'ro', label='measured')
    plt.xlabel('energy (eV)')
    plt.ylabel('angle (degrees)')
    plt.title(thistitle)
    plt.text(12000, y1, 'd-spacing = %.8f ± %.8f Å' % (d_spacing, derr), fontsize='small')
    plt.text(12000, y2, 'offset = %.5f ± %.5f degrees' % (offset, oerr), fontsize='small')
    legend = plt.legend(loc='upper right', shadow=True)
    plt.show()
    
    plottheta = numpy.arange(20.0, 5.0,-0.1)
    if mono == '311':
        plottheta = numpy.arange(36.0,10.0,-0.1)
