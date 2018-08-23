
import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import numpy
import os

from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

run_report(__file__)



#areaplot = DerivedPlot(func,
#                       xlabel=thismotor.name,
#                       ylabel=detector+denominator)



def areascan():
    RE.msg_hook = None
    #areaplot = LiveScatter('xafs_liny', 'xafs_linx', 'quadem1_I0',
    #                       xlim=(-3,3), ylim=(-3,3))
    areafunc = lambda doc: (doc['data'][xafs_linx.name], doc['data'][xafs_liny.name], doc['data']['It'])
    areaplot = DerivedPlot(areafunc,
                           xlabel=xafs_liny.name,
                           ylabel=xafs_linx.name)
    @subs_decorator(areaplot)
    def make_areascan():
        yield from rel_grid_scan([quadem1],
                                 xafs_liny, -3, 3, 7,
                                 xafs_linx, -3, 3, 7, False)
    yield from make_areascan()
    RE.msg_hook = BMM_msg_hook
