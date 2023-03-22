
import matplotlib.pyplot as plt
from lmfit.models import SkewedGaussianModel, RectangleModel
import numpy
from scipy.interpolate import interp1d

from larch_interface import Pandrosus, Kekropidai
from slack import img_to_slack, post_to_slack

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)


def finished(record):
    if 'num' in record.metadata['start']['plan_args']:  # 1D scan
        expected = record.metadata['start']['plan_args']['num']
    else:                       # 2D scan
        expected = record.metadata['start']['num_points']        
    executed = record.metadata['stop']['num_events']['primary']
    if expected != executed:    # scan did not run to completion
        return False
    return True

def checkhint(hint, which):
    if hint.startswith(which) is False:
        print(f'plot_{which}: hint mismatch, how did you get here?')
        return False
    return True

def plot_linescan(bmm_catalog, uid):
    record = bmm_catalog[uid]
    if finished(record) is False: return
    hint = record.metadata['start']['BMM_kafka']['hint']
    if checkhint(hint, 'linescan') is False: return
    detector, motor = hint.split()[1:]

    table = record.primary.read()

    if detector == 'It':
        signal, label, title = table['It']/table['I0'], 'It/I0', f'transmission vs. {motor}'
    elif detector == 'Ir':
        signal, label, title = table['Ir'], 'Ir', f'reference vs. {motor}'
    elif detector == 'I0':
        signal, label, title = table['I0'], 'I0', f'I0 vs. {motor}'
    elif detector == 'I0a':
        signal, label, title = table['I0a']/table['I0'], 'I0a', f'I0a & I0b vs. {motor}'
        signal2 = table['I0b']/table['I0']
    elif detector == 'I0b':
        signal, label, title = table['I0b']/table['I0'], 'I0b', f'I0a & I0b vs. {motor}'
        signal2 = table['I0a']/table['I0']
    elif detector == 'Iy':
        signal, label, title = table['Iy']/table['I0'], 'Iy/I0', f'yield vs. {motor}'
    elif detector == 'If' or detector == 'Xs':
        xs1, xs2, xs3, xs4 = rkvs.get('BMM:user:xs1'), rkvs.get('BMM:user:xs2'), rkvs.get('BMM:user:xs3'), rkvs.get('BMM:user:xs4')
        signal = (table[xs1]+table[xs2]+table[xs3]+table[xs4]) / table['I0']
        label = 'If/I0'
        title = f'4 element fluorescence vs. {motor}'
    elif detector == 'Xs1':
        xs8 = rkvs.get('BMM:user:xs8')
        signal = table[xs8] / table['I0']
        label = 'If/I0'
        title = f'1 element fluorescence vs. {motor}'


    # Tom's explanation for how to do multiple plots: https://stackoverflow.com/a/31686953
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(table[motor], signal, label=label)
    if detector == 'I0a':
        ax.plot(table[motor], signal2, label='I0b')
    if detector == 'I0b':
        ax.plot(table[motor], signal2, label='I0a')
    ax.set_facecolor((0.95, 0.95, 0.95))
    ax.set_title(title)
    ax.set_xlabel(motor)
    ax.set_ylabel(label)
    plt.gca().legend()
    fig.canvas.manager.show()
    fig.canvas.flush_events() 
        
        
def plot_timescan(bmm_catalog, uid):
    record = bmm_catalog[uid]
    if finished(record) is False: return
    hint = record.metadata['start']['BMM_kafka']['hint']
    if checkhint(hint, 'timescan') is False: return
    detector = hint.split()[1]

    table = record.primary.read()

    if detector == 'It':
        signal, label, title = table['It'], 'It', 'It time scan'
    elif detector == 'Transmission':
        signal, label, title = numpy.log(table['I0']/table['It']), 'ln(I0/It)', 'transmission time scan'
    elif detector == 'Ir':
        signal, label, title = table['Ir'], 'Ir', 'Ir time scan'
    elif detector == 'Reference':
        signal, label, title = numpy.log(table['It']/table['Ir']), 'ln(It/Ir)', 'reference time scan'
    elif detector == 'I0':
        signal, label, title = table['I0'], 'I0', 'I0 time scan'
    elif detector == 'Iy':
        signal, label, title = table['Iy'], 'Iy', 'Iy time scan'
    elif detector == 'Yield':
        signal, label, title = table['Iy']/table['I0'], 'Iy/I0', 'yield time scan'
    elif detector == 'Fluorescence' or detector == 'Xs':
        xs1, xs2, xs3, xs4 = rkvs.get('BMM:user:xs1'), rkvs.get('BMM:user:xs2'), rkvs.get('BMM:user:xs3'), rkvs.get('BMM:user:xs4')
        signal = (table[xs1]+table[xs2]+table[xs3]+table[xs4]) / table['I0']
        label  = 'If/I0'
        title  = '4 element fluorescence time scan'
    elif detector == 'If':
        xs1, xs2, xs3, xs4 = rkvs.get('BMM:user:xs1'), rkvs.get('BMM:user:xs2'), rkvs.get('BMM:user:xs3'), rkvs.get('BMM:user:xs4')
        signal = table[xs1]+table[xs2]+table[xs3]+table[xs4]
        label  = 'If'
        title  = '4 element If time scan'
    elif detector == 'Xs1':
        xs8    = rkvs.get('BMM:user:xs8')
        signal = table[xs8] / table['I0']
        label  = 'If/I0'
        title  = '1 element fluorescence time scan'


    # Tom's explanation for how to do multiple plots: https://stackoverflow.com/a/31686953
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(table['time']-table['time'][0], signal)
    ax.set_facecolor((0.95, 0.95, 0.95))
    ax.set_title(title)
    ax.set_xlabel('time (sec)')
    ax.set_ylabel(label)
    fig.canvas.manager.show()
    fig.canvas.flush_events() 


def plot_rectanglescan(bmm_catalog, uid):
    record = bmm_catalog[uid]
    if finished(record) is False: return
    hint = record.metadata['start']['BMM_kafka']['hint']
    if checkhint(hint, 'rectanglescan') is False: return
    detector, motor, negated = hint.split()[1:]

    table = record.primary.read()

    if detector.lower() == 'if':
        xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
        xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
        xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
        xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
        signal   = numpy.array((table[xs1]+table[xs2]+table[xs3]+table[xs4])/table['I0'])
    elif detector.lower() == 'it':
        signal   = numpy.array(table['It']/table['I0'])
    elif detector.lower() == 'ir':
        signal   = numpy.array(table['Ir']/table['It'])
    
    signal = signal - signal[0]
    if negated == 'negated':
        signal = -1 * signal

    pos      = numpy.array(table[motor])
    mod      = RectangleModel(form='erf')
    pars     = mod.guess(signal, x=pos)
    out      = mod.fit(signal, pars, x=pos)
    #print(out.fit_report(min_correl=0))
    out.plot(xlabel=motor, ylabel=detector)

def plot_areascan(bmm_catalog, uid):
    record = bmm_catalog[uid]
    if finished(record) is False: return
    hint = record.metadata['start']['BMM_kafka']['hint']
    if checkhint(hint, 'areascan') is False: return
    detector, slow, fast, contour, log, energy = hint.split()[1:]
    pngout = record.metadata['start']['BMM_kafka']['pngout']
    nslow, nfast = record.metadata['start']['shape']
    try:
        fname = record.metadata['start']['BMM_kafka']['pngout']
    except:
        fname = None
        
    table = record.primary.read()

    x=numpy.array(table[fast])
    y=numpy.array(table[slow])
    xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
    xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
    xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
    xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
    if detector.lower() == 'noisy_det':
        z=numpy.array(table['noisy_det'])
    elif detector.lower() == 'it':
        z=numpy.array(table['It'])
    elif detector.lower() == 'xs':
        z=numpy.array(table[xs1]) + numpy.array(table[xs2]) + numpy.array(table[xs3]) + numpy.array(table[xs4])
    else:
        z=numpy.array(table[xs1]) + numpy.array(table[xs2]) + numpy.array(table[xs3]) + numpy.array(table[xs4])

    z=z.reshape(nslow, nfast)
    if log == 'True':
        z = numpy.log(z)
        
    fig = plt.figure()
    fig.set_facecolor((0.95, 0.95, 0.95))
    plt.title(f'{detector}     Energy = {energy}')
    plt.xlabel(f'fast axis ({fast}) position (mm)')
    plt.ylabel(f'slow axis ({slow}) position (mm)')
    plt.gca().invert_yaxis()  # plot an xafs_x/xafs_y plot upright
    if contour == 'True':
        plt.contourf(x[:nfast], y[::nfast], z, cmap=plt.cm.viridis)
    else:
        plt.pcolormesh(x[:nfast], y[::nfast], z, cmap=plt.cm.viridis)
    plt.colorbar()
    if pngout is not None and pngout.strip() != '':
        plt.savefig(pngout)
        img_to_slack(pngout)
    plt.show()


def plot_xafs(bmm_catalog, uid):
    record = bmm_catalog[uid]
    if finished(record) is False: return
    metadata = record.metadata['start']['BMM_kafka']
    hint = metadata['hint']
    mode = hint.split()[1]
    if checkhint(hint, 'xafs') is False: return
    this = Pandrosus()
    this.element, this.edge, this.folder, this.db = metadata['element'], metadata['edge'], metadata['folder'], bmm_catalog
    this.facecolor = (0.95, 0.95, 0.95)
    this.fetch(uid=uid, mode=mode)
    this.title = f"{metadata['filename']}  scan {metadata['count']}/{metadata['repetitions']}"
    this.triplot()
    

def wafer_plot(**kwargs):
    uid       = kwargs['uid']
    motor     = kwargs['motor']
    center    = kwargs['center']
    amplitude = kwargs['amplitude']
    xaxis     = kwargs['xaxis']
    data      = kwargs['data']
    best_fit  = kwargs['best_fit']

    direction = motor.split('_')[1]

    fig = plt.figure()
    ax = fig.gca()
    ax.scatter(xaxis, data, color='blue')
    ax.plot(xaxis, best_fit, color='red')
    ax.scatter(center, amplitude/2, s=160, marker='x', color='green')
    ax.set_facecolor((0.95, 0.95, 0.95))
    ax.set_xlabel(f'{motor} (mm)')
    ax.set_ylabel(f'It/I0 and error function')
    ax.set_title(f'Wafer edge: {direction} scan, center={center:.3f}')
    fig.canvas.manager.show()
    fig.canvas.flush_events() 
    
    
def mono_calibration_plot(**kwargs):
    found    = kwargs['found']
    ee       = kwargs['ee']
    tt       = kwargs['tt']
    mono     = kwargs['mono']
    dspacing = kwargs['dspacing']
    offset   = kwargs['offset']

    y1, y2 = 13.5, 12.9
    if mono == '311':
        y1, y2 = 2*y1, 2*y2
    
    ## cubic interpolation of tabulated edge energies
    xnew = numpy.linspace(min(ee),max(ee),100)
    f = interp1d(ee, tt, kind='cubic')
        
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(xnew, f(xnew), label='tabulated')
    ax.plot(found, tt, 'ro', label='measured')
    ax.set_facecolor((0.95, 0.95, 0.95))
    ax.set_xlabel('energy (eV)')
    ax.set_ylabel('angle (degrees)')
    ax.set_title(f'Si({mono}) calibration curve')
    ax.text(12000, y1, f'd-spacing = {dspacing[0]:.8f} ± {dspacing[1]:.8f} Å', fontsize='small')
    ax.text(12000, y2, f'offset = {offset[0]:.5f} ± {offset[1]:.5f} degrees', fontsize='small')
    ax.legend(loc='upper right', shadow=True)
    fig.canvas.manager.show()
    fig.canvas.flush_events() 

    
