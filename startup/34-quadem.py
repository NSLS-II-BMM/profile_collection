from ophyd import EpicsSignal
from BMM.electrometer import BMMQuadEM, BMMDualEM

run_report(__file__)

        
quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')

quadem1.I0.kind = 'hinted'
quadem1.It.kind = 'hinted'
quadem1.Ir.kind = 'hinted'
quadem1.Iy.kind = 'omitted'      # 'hinted'

quadem1.I0.name = 'I0'
quadem1.It.name = 'It'
quadem1.Ir.name = 'Ir'
quadem1.Iy.name = 'Iy'


## need to do something like this:
##    caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 7
## to get a sensible reporting precision from the Ix channels
def set_precision(pv, val):
    EpicsSignal(pv.pvname + ".PREC", name='').put(val)

set_precision(quadem1.current1.mean_value, 3)
toss = quadem1.I0.describe()
set_precision(quadem1.current2.mean_value, 3)
toss = quadem1.It.describe()
set_precision(quadem1.current3.mean_value, 3)
toss = quadem1.Ir.describe()
set_precision(quadem1.current4.mean_value, 3)
toss = quadem1.Iy.describe()



        
dualio = BMMDualEM('XF:06BM-BI{EM:3}EM180:', name='DualI0')
dualio.Ia.kind = 'hinted'
dualio.Ib.kind = 'hinted'
dualio.Ia.name = 'Ia'
dualio.Ib.name = 'Ib'



quadem2 = BMMQuadEM('XF:06BM-BI{EM:2}EM180:', name='quadem2')


def dark_current():
    reopen = shb.state.get() == shb.openval 
    if reopen:
        print('\nClosing photon shutter')
        yield from shb.close_plan()
    print('Measuring current offsets, this will take several seconds')
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset1.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset2.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset3.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset4.PROC", name='').put(1)
    yield from sleep(3)
    BMM_log_info('Measured dark current on quadem1')
    if reopen:
        print('Opening photon shutter')
        yield from shb.open_plan()
        print('You are ready to measure!\n')

    
