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
    xnew = np.linspace(min(ee),max(ee),300)
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
