from bluesky.plan_stubs import sleep, mv, mvr, null


from IPython import get_ipython
user_ns = get_ipython().user_ns


class DetectorMount():
    def __init__(self):
        self.motor = user_ns['xafs_det']
        self.low   = 10
        self.high  = 210
        self.sampley = user_ns['xafs_x']
        self.margin = 15


    def far(self):
        yield from mv(self.motor, self.high)

    def near(self):
        yield from mv(self.motor, self.low)

    def tweak(self, val):
        yield from mvr(self.motor, val)
        

        
    def separation(self):
        return(self.motor.position - self.sampley.position)
    
