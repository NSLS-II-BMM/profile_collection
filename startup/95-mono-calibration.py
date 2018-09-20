import configparser
config = configparser.ConfigParser()

import lmfit

import pprint
pp = pprint.PrettyPrinter(indent=4)
from numpy import array


def calibrate_mono():
    # read content from INI file
    config.read_file(open('/home/xf06bm/Data/Staff/mono_calibration/edges111.ini'))
    mono      = config.get('config', 'mono')
    DSPACING  = float(config.get('config', 'DSPACING'))
    thistitle = config.get('config', 'thistitle')

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
    offset = fit.params.get('offset').value
    energy = (2*pi*HBARC) / (2*d_spacing*sin((theta+offset)*pi/180))

    i = 0
    print('')
    for el in ordered:
        val = (2*pi*HBARC) / (2*d_spacing*sin((tt[i]+offset)*pi/180))
        print("%-2s  %9.3f  %9.3f  %9.3f" % (el, ee[i], val, val-ee[i]))
        i = i+1
    print('')

    plottheta = numpy.arange(20.0, 5.0,-0.1)
    if mono == '311':
        plottheta = numpy.arange(36.0,10.0,-0.1)
