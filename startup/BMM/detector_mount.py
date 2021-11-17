from bluesky.plan_stubs import sleep, mv, mvr, null
from bluesky.plans import count

from numpy import array, sqrt, log, ceil, floor
from lmfit.models import ExponentialModel

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.motors import xafs_det, xafs_x

class DetectorMount():
    def __init__(self):
        self.motor = xafs_det
        self.low   = 10
        self.high  = 205
        self.sampley = xafs_x
        self.margin = 15


    def far(self):
        yield from mv(self.motor, self.high)

    def near(self):
        yield from mv(self.motor, self.low)

    def tweak(self, val):
        yield from mvr(self.motor, val)
        
    def is_close(self):
        if (self.motor.position - self.low < 10):
            return True
        else:
            return False
        
    def separation(self):
        return(self.motor.position - self.sampley.position)
    


import time
from BMM.logging import BMM_msg_hook
from BMM.functions import go_msg, whisper


def predict_detector_position(datatable=None, target=20500):
    dt = array(datatable)
    mod    = ExponentialModel()
    prediction = []
    for i in range(1,5):
        signal = dt[:,i]
        pars   = mod.guess(signal, x=dt[:,0])
        out    = mod.fit(signal, pars, x=dt[:,0])
        #out.plot()
        #print(whisper(out.fit_report(min_correl=0)))
        amp = out.params['amplitude']
        tau = out.params['decay']
        prediction.append(ceil(tau * log(amp/target)))
    #print(go_msg(f'predictions are {prediction}'))
    return prediction

def find_detector_position(start=205, inttime=0.1, verbose=True):
    RE, xafs_det, dwell_time, xs = user_ns['RE'], user_ns['xafs_det'], user_ns['dwell_time'], user_ns['xs']

    RE.msg_hook = None

    # if step == 0:
    #     step = -5
    # if step > 0:
    #     step = -1 * step
    step = 5
    factor = 1/inttime
    toomuch = 205000. / factor
    description = 'optimized'

    datatable = []
    
    yield from mv(xafs_det, start)
    yield from mv(dwell_time, inttime)

    yield from mv(xs.cam.acquire, 1)
    time.sleep(0.25)
    ocrs = [float(xs.channels.channel01.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel02.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel03.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel04.mcarois.mcaroi16.total_rbv.get())]
    datatable.append([xafs_det.position, *ocrs])
    if verbose:
        print(' xafs_det  OCR 1     OCR 2     OCR 3     OCR 4   target      predictions')
        print('=======================================================================================')
        print(f' {xafs_det.position:5.1f}   {ocrs[0]:8.1f}  {ocrs[1]:8.1f}  {ocrs[2]:8.1f}  {ocrs[3]:8.1f}  {toomuch}')
    
    while all(y < toomuch for y in ocrs):
        if xafs_det.position - xafs_det.llm.get() < 10:
            step = -1
        elif xafs_det.position - xafs_det.llm.get() < 30:
            step = -2
        elif xafs_det.position - xafs_det.llm.get() < 80:
            step = -5
        else:
            step = -10
            
        if xafs_det.position + step < xafs_det.llm.get():
            description = 'closest possible'
            print(whisper(f'the next step would go below the xafs_det soft limit ({xafs_det.llm.get()})'))
            break
        yield from mvr(xafs_det, step)

        yield from mv(xs.cam.acquire, 1)
        time.sleep(1.5*inttime)
        ocrs = [float(xs.channels.channel01.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel02.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel03.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel04.mcarois.mcaroi16.total_rbv.get())]
        datatable.append([xafs_det.position, *ocrs])
        if verbose:
            if len(datatable) > 5:
                predictions = predict_detector_position(datatable, toomuch)
                print(f' {xafs_det.position:5.1f}   {ocrs[0]:8.1f}  {ocrs[1]:8.1f}  {ocrs[2]:8.1f}  {ocrs[3]:8.1f}  {toomuch}  {predictions[0]}  {predictions[1]}  {predictions[2]}  {predictions[3]}')
            else:
                print(f' {xafs_det.position:5.1f}   {ocrs[0]:8.1f}  {ocrs[1]:8.1f}  {ocrs[2]:8.1f}  {ocrs[3]:8.1f}  {toomuch}')

            
    if verbose:
        yield from mv(dwell_time, 1.0)
        #yield from mv(xs.total_points, 1)
        #yield from count([xs], 1)
        #yield from sleep(0.25)
        #xs.table()
        #xs.plot(add=True)
        xs.measure_xrf(doplot=False)
        print(whisper('make a plot with: xs.plot()'))

        
    yield from mv(dwell_time, 0.5)
    RE.msg_hook = BMM_msg_hook
    print(f'\nfound {description} detector position at ' + go_msg(f'{xafs_det.position:5.1f}'))
    return xafs_det.position
