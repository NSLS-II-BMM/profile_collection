import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import numpy
import os

from bluesky.preprocessors import subs_decorator
## see 88-plot-hacking.py for definitions of plot functions for DerivedPlot
## see 10-motors.py and 20-dcm.py for motor definitions

def slit_height(start=-3.0, stop=3.0, nsteps=61):
    plot = DerivedPlot(bctscan, xlabel='slit height', ylabel='I0')
    motor = dm3_bct

    BMM_log_info('slit height scan: %s, %s, %.3f, %.3f, %d -- starting at %.3f'
                 % (motor.name, 'i0', start, stop, nsteps, motor.user_readback.value))

    @subs_decorator(plot)
    def scan_slit():
        yield from abs_set(quadem1.averaging_time, 0.1)
        yield from abs_set(motor.kill_cmd, 1)

        yield from rel_scan([quadem1], motor, start, stop, nsteps)

        yield from bps.sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(motor.kill_cmd, 1)

    yield from scan_slit()
    BMM_log_info('slit height scan finished, uid = %s, scan_id = %d' %
                 (db[-1].start['uid'], db[-1].start['scan_id']))


def rocking_curve(start=-0.15, stop=0.15, nsteps=151):
    plot = DerivedPlot(dcmpitch, xlabel='2nd crystal pitch', ylabel='I0')
    motor = dcm_pitch

    BMM_log_info('rocking curve scan: %s, %s, %.3f, %.3f, %d -- starting at %.3f'
                 % (motor.name, 'i0', start, stop, nsteps, motor.user_readback.value))

    @subs_decorator(plot)
    def scan_dcmpitch():
        yield from abs_set(quadem1.averaging_time, 0.1)
        yield from abs_set(motor.kill_cmd, 1)

        yield from rel_scan([quadem1], motor, start, stop, nsteps)

        t  = db[-1].table()
        maxval = t['I0'].max()
        top = float(t[t['I0'] == maxval]['dcm_pitch']) # position of max intensity
        ## see https://pandas.pydata.org/pandas-docs/stable/10min.html#boolean-indexing

        yield from bps.sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(motor.kill_cmd, 1)

        yield from mv(motor, top)
        yield from bps.sleep(3.0)
        yield from abs_set(motor.kill_cmd, 1)

    yield from scan_dcmpitch()
    BMM_log_info('rocking curve scan finished, uid = %s, scan_id = %d' %
                 (db[-1].start['uid'], db[-1].start['scan_id']))



####################################
# generic linescan vs. It/If/Ir/I0 #
####################################
def linescan(axis, detector, start, stop, nsteps): # inegration time?

    ##        linear stages        tilt stage           rotation stages
    motors = {'x'    : xafs_linx,  'roll' : xafs_roll,  'roth' : xafs_roth,
              'y'    : xafs_liny,  'pitch': xafs_pitch, 'rotb' : xafs_rotb,
              's'    : xafs_lins,                       'rots' : xafs_rots,
              'xs'   : xafs_linxs,
          }

    ## sanitize input and set thismotor to an actual motor
    if type(axis) is str:
        axis      = axis.lower()
    detector  = detector.capitalize()
    if 'EpicsMotor' in str(type(axis)):
        thismotor = axis
    else:                       # presume it's an xafs_XXXX motor
        thismotor = motors[axis]

    ## sanity checks on input
    if axis not in motors.keys() and 'EpicsMotor' not in str(type(axis)):
        print(colored('\n*** %s is not a linescan motor (%s)\n' %
                      (axis, str.join(', ', motors.keys())), color='red'))
        yield from null()
        return
    if detector not in ('It', 'If'):
        print(colored('\n*** %s is not a linescan measurement (%s)\n' %
                      (detector, 'it, if'), color='red'))
        yield from null()
        return

    dets  = [quadem1,]
    denominator = ''

    ## func is an anonymous function, built on the fly, for feeding to DerivedPlot
    if detector == 'It':
        denominator = ' / I0'
        func = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
    elif detector == 'Ir':
        denominator = ' / It'
        func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ir']/doc['data']['It'])
    elif detector == 'I0':
        func = lambda doc: (doc['data'][thismotor.name], doc['data']['I0'])
    elif detector == 'If':
        dets.append(vor)
        denominator = ' / I0'
        func = lambda doc: (doc['data'][thismotor.name],
                            (doc['data']['DTC1'] +
                             doc['data']['DTC2'] +
                             doc['data']['DTC3'] +
                             doc['data']['DTC4']   ) / doc['data']['I0'])
    ## and this is the appropriate way to plot this linescan
    plot = DerivedPlot(func,
                       xlabel=thismotor.name,
                       ylabel=detector+denominator)

    BMM_log_info('linescan: %s, %s, %.3f, %.3f, %d -- starting at %.3f' %
                 (thismotor.name, detector, start, stop, nsteps, thismotor.user_readback.value))

    @subs_decorator(plot)
    def scan_xafs_motor(dets, motor, start, stop, nsteps):
        yield from rel_scan(dets, motor, start, stop, nsteps)

    yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
    BMM_log_info('linescan finished, uid = %s, scan_id = %d' %
                 (db[-1].start['uid'], db[-1].start['scan_id']))


    # if axis == 'x':
    #     motor = xafs_linx
    #     if detector == 'it':
    #         plot  = DerivedPlot(xscan, xlabel='sample X', ylabel='It / I0')
    #     elif detector == 'if':
    #         plot  = DerivedPlot(dt_x,  xlabel='sample X', ylabel='If / I0')
    #         dets.append(vor)

    # elif axis == 'q':
    #     dets  = [quadem1,]
    #     motor = xafs_liny
    #     #text  = 'def qscan(doc): return (doc[\'data\'][\'xafs_liny\'], doc[\'data\'][\'It\'])'
    #     #func = eval(text)
    #     func = lambda doc: (doc['data']['xafs_liny'], doc['data']['It'])
    #     plot  = DerivedPlot(func, xlabel='sample Q', ylabel='It')


    # elif axis == 'y':
    #     motor = xafs_liny
    #     dets  = [quadem1,]
    #     if detector == 'it':
    #         plot  = DerivedPlot(yscan, xlabel='sample X', ylabel='It / I0')
    #     elif detector == 'if':
    #         plot  = DerivedPlot(dt_y,  xlabel='sample X', ylabel='If / I0')
    #         dets.append(vor)

    # elif axis == 'roll':
    #     motor = xafs_roll
    #     dets  = [quadem1,]
    #     if detector == 'it':
    #         plot  = DerivedPlot(rollscan_trans, xlabel='sample roll', ylabel='It / I0')
    #     elif detector == 'if':
    #         plot  = DerivedPlot(rollscan_fluo,  xlabel='sample roll', ylabel='If / I0')
    #         dets.append(vor)

    # elif axis == 'pitch':
    #     motor = xafs_pitch
    #     dets  = [quadem1,]
    #     if detector == 'it':
    #         plot  = DerivedPlot(pitchscan_trans, xlabel='sample roll', ylabel='It / I0')
    #     elif detector == 'if':
    #         plot  = DerivedPlot(pitchscan_fluo,  xlabel='sample roll', ylabel='If / I0')
    #         dets.append(vor)



#############################################################
# extract a linescan from the database, write an ascii file #
#############################################################
def ls2dat(datafile, key):
    if os.path.isfile(datafile):
        print(colored('%s already exists!  Bailing out....' % datafile, color='red'))
        return
    handle = open(datafile, 'w')
    dataframe = db[key]
    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    if 'vor' in devices:
        abscissa = (devices - {'quadem1', 'vor'}).pop()
        column_list = [abscissa, 'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        abscissa = (devices - {'quadem1',}).pop()
        template = "  %.3f  %.6f  %.6f  %.6f\n"
        column_list = [abscissa, 'I0', 'It', 'Ir']

    table = dataframe.table()
    this = table.loc[:,column_list]

    handle.write('# ' + '  '.join(column_list) + '\n')
    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
    print(colored('wrote %s' % datafile, color='white'))
