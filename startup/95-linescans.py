import bluesky as bs
import bluesky.plans as bp
import numpy
import os


def slit_height(start=-3.0, stop=3.0, nsteps=61):
    yield from abs_set(quadem1.averaging_time, 0.1)
    yield from abs_set(dm3_bct.kill_cmd, 1)

    yield from rel_scan([quadem1], dm3_bct, start, stop, nsteps)

    yield from sleep(3.0)
    yield from abs_set(quadem1.averaging_time, 0.5)
    yield from abs_set(dm3_bct.kill_cmd, 1)


def rocking_curve(start=-0.15, stop=0.15, nsteps=151):
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
