from bluesky.plan_stubs import sleep, mv, mvr, null


from IPython import get_ipython
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
    
