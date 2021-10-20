from bluesky.plan_stubs import sleep, mv, mvr, null


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
from BMM.functions import go_msg



def find_detector_position(start=205, step=-5, inttime=0.1, verbose=True):
    RE, xafs_det, dwell_time, xs = user_ns['RE'], user_ns['xafs_det'], user_ns['dwell_time'], user_ns['xs']

    RE.msg_hook = None

    if step == 0:
        step = -5
    if step > 0:
        step = -1 * step
    factor = 1/inttime
    toomuch = 205000. / factor

    yield from mv(xafs_det, start)
    yield from mv(dwell_time, inttime)

    yield from mv(xs.cam.acquire, 1)
    time.sleep(0.25)
    ocrs = [float(xs.channels.channel01.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel02.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel03.mcarois.mcaroi16.total_rbv.get()),
            float(xs.channels.channel04.mcarois.mcaroi16.total_rbv.get())]
    if verbose:
        print('  OCR 1     OCR 2     OCR 3     OCR 4   target   xafs_det')
        print('=========================================================')
    
    while all(y < toomuch for y in ocrs):
        if verbose:
            print(f'{ocrs[0]:8.1f}  {ocrs[1]:8.1f}  {ocrs[2]:8.1f}  {ocrs[3]:8.1f}  {toomuch}  {xafs_det.position:5.1f}')
        if xafs_det.position - 5 < xafs_det.llm.get():
            break
        yield from mvr(xafs_det, step)

        yield from mv(xs.cam.acquire, 1)
        time.sleep(1.5*inttime)
        ocrs = [float(xs.channels.channel01.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel02.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel03.mcarois.mcaroi16.total_rbv.get()),
                float(xs.channels.channel04.mcarois.mcaroi16.total_rbv.get())]
        
    yield from mv(dwell_time, 0.5)
    print('\nfound optimized detector position at ' + go_msg(f'{xafs_det.position:5.1f}'))
    RE.msg_hook = BMM_msg_hook
    xs.measure_xrf()
    return xafs_det.position
