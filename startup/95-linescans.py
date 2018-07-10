import bluesky as bs
import bluesky.plans as bp
import numpy
import os

from bluesky.preprocessors import subs_decorator

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

        yield from sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(motor.kill_cmd, 1)

    yield from scan_slit()


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

        df = db[-1]
        t  = df.table()
        maxval = t['I0'].max()
        top = float(t[t['I0'] == maxval]['dcm_pitch']) # position of max intensity
        ## see https://pandas.pydata.org/pandas-docs/stable/10min.html#boolean-indexing

        yield from sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(motor.kill_cmd, 1)

        yield from mv(motor, top)
        yield from sleep(3.0)
        yield from abs_set(motor.kill_cmd, 1)

    yield from scan_dcmpitch()

def linescan(axis, detector, start, stop, nsteps):
    motors = ('x', 'y', 'roll', 'pitch') # roth, rotb, rots, linxs, linx

    axis = axis.lower()
    detector = detector.lower()

    if axis not in ('x', 'y', 'roll', 'pitch'):
        print(colored('\n*** %s is not a linescan motor (%s)\n' % (axis, str.join(', ', motors)), color='red'))
        yield from null()
        return
    if detector not in ('it', 'if'):
        print(colored('\n*** %s is not a linescan measurement (%s)\n' % (detector, 'it, if'), color='red'))
        yield from null()
        return

    if axis == 'x':
        motor = xafs_linx
        dets  = [quadem1,]
        if detector == 'it':
            plot  = DerivedPlot(xscan, xlabel='sample X', ylabel='It / I0')
        elif detector == 'if':
            plot  = DerivedPlot(dt_x,  xlabel='sample X', ylabel='If / I0')
            dets.append(vor)

    elif axis == 'y':
        motor = xafs_liny
        dets  = [quadem1,]
        if detector == 'it':
            plot  = DerivedPlot(yscan, xlabel='sample X', ylabel='It / I0')
        elif detector == 'if':
            plot  = DerivedPlot(dt_y,  xlabel='sample X', ylabel='If / I0')
            dets.append(vor)

    elif axis == 'roll':
        motor = xafs_roll
        dets  = [quadem1,]
        if detector == 'it':
            plot  = DerivedPlot(rollscan_trans, xlabel='sample roll', ylabel='It / I0')
        elif detector == 'if':
            plot  = DerivedPlot(rollscan_fluo,  xlabel='sample roll', ylabel='If / I0')
            dets.append(vor)

    elif axis == 'pitch':
        motor = xafs_pitch
        dets  = [quadem1,]
        if detector == 'it':
            plot  = DerivedPlot(pitchscan_trans, xlabel='sample roll', ylabel='It / I0')
        elif detector == 'if':
            plot  = DerivedPlot(pitchscan_fluo,  xlabel='sample roll', ylabel='If / I0')
            dets.append(vor)

    BMM_log_info('linescan: %s, %s, %.3f, %.3f, %d -- starting at %.3f'
                 % (motor.name, detector, start, stop, nsteps, motor.user_readback.value))

    @subs_decorator(plot)
    def scan_xafs_motor(dets, motor, start, stop, nsteps):
        yield from rel_scan(dets, motor, start, stop, nsteps)

    yield from scan_xafs_motor(dets, motor, start, stop, nsteps)
