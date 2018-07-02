import bluesky as bs
import bluesky.plans as bp
import numpy
import os

from bluesky.preprocessors import subs_decorator

def slit_height(start=-3.0, stop=3.0, nsteps=61):
    plot = DerivedPlot(bctscan, xlabel='slit height', ylabel='I0')

    @subs_decorator(plot)
    def scan_slit():
        yield from abs_set(quadem1.averaging_time, 0.1)
        yield from abs_set(dm3_bct.kill_cmd, 1)

        yield from rel_scan([quadem1], dm3_bct, start, stop, nsteps)

        yield from sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(dm3_bct.kill_cmd, 1)

    yield from scan_slit()


def rocking_curve(start=-0.15, stop=0.15, nsteps=151):
    plot = DerivedPlot(dcmpitch, xlabel='2nd crystal pitch', ylabel='I0')

    @subs_decorator(plot)
    def scan_dcmpitch():
        yield from abs_set(quadem1.averaging_time, 0.1)
        yield from abs_set(dcm_pitch.kill_cmd, 1)

        yield from rel_scan([quadem1], dcm_pitch, start, stop, nsteps)

        df = db[-1]
        t  = df.table()
        maxval = t['I0'].max()
        top = float(t[t['I0'] == maxval]['dcm_pitch']) # position of max intensity
        ## see https://pandas.pydata.org/pandas-docs/stable/10min.html#boolean-indexing

        yield from sleep(3.0)
        yield from abs_set(quadem1.averaging_time, 0.5)
        yield from abs_set(dcm_pitch.kill_cmd, 1)

        yield from mv(dcm_pitch, top)
        yield from sleep(3.0)
        yield from abs_set(dcm_pitch.kill_cmd, 1)

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

    if axis == 'x' and detector == 'it':
        plot  = DerivedPlot(xscan, xlabel='sample X', ylabel='It / I0')
        motor = xafs_linx
        dets  = [quadem1,]
    elif axis == 'x' and detector == 'if':
        plot  = DerivedPlot(dt_x,  xlabel='sample X', ylabel='If / I0')
        motor = xafs_linx
        dets  = [quadem1, vor]

    elif axis == 'y' and detector == 'it':
        plot  = DerivedPlot(yscan, xlabel='sample Y', ylabel='It / I0')
        motor = xafs_liny
        dets  = [quadem1,]
    elif axis == 'y' and detector == 'if':
        plot  = DerivedPlot(dt_y,  xlabel='sample Y', ylabel='If / I0')
        motor = xafs_liny
        dets  = [quadem1, vor]

    elif axis == 'roll' and detector == 'it':
        plot  = DerivedPlot(rollscan_trans, xlabel='sample roll', ylabel='It / I0')
        motor = xafs_roll
        dets  = [quadem1,]
    elif axis == 'roll' and detector == 'if':
        plot  = DerivedPlot(rollscan_fluo,  xlabel='sample roll', ylabel='If / I0')
        motor = xafs_roll
        dets  = [quadem1, vor]

    elif axis == 'pitch' and detector == 'it':
        plot  = DerivedPlot(pitchscan_trans, xlabel='sample pitch', ylabel='It / I0')
        motor = xafs_pitch
        dets  = [quadem1,]
    elif axis == 'pitch' and detector == 'if':
        plot  = DerivedPlot(pitchscan_fluo,  xlabel='sample pitch', ylabel='If  /  I0')
        motor = xafs_pitch
        dets  = [quadem1, vor]

    @subs_decorator(plot)
    def scan_xafs_motor(dets, motor, start, stop, nsteps):
        yield from rel_scan(dets, motor, start, stop, nsteps)

    yield from scan_xafs_motor(dets, motor, start, stop, nsteps)
