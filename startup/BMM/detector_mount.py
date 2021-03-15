from bluesky.plan_stubs import sleep, mv, mvr, null

try:
    from bluesky_queueserver.manager.profile_tools import set_user_ns
except ModuleNotFoundError:
    from ._set_user_ns import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns


class DetectorMount():

    @set_user_ns
    def __init__(self, *, user_ns):
        self.motor = user_ns['xafs_det']
        self.low   = 10
        self.high  = 205
        self.sampley = user_ns['xafs_x']
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
    
