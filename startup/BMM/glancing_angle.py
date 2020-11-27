
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device



class GlancingAngle(Device):
    spinner1 = Cpt(EpicsSignal, 'OutPt08:Data-Sel')
    spinner2 = Cpt(EpicsSignal, 'OutPt09:Data-Sel')
    spinner3 = Cpt(EpicsSignal, 'OutPt10:Data-Sel')
    spinner4 = Cpt(EpicsSignal, 'OutPt11:Data-Sel')
    spinner5 = Cpt(EpicsSignal, 'OutPt12:Data-Sel')
    spinner6 = Cpt(EpicsSignal, 'OutPt13:Data-Sel')
    spinner7 = Cpt(EpicsSignal, 'OutPt14:Data-Sel')
    spinner8 = Cpt(EpicsSignal, 'OutPt15:Data-Sel')
    #rotation
    
    def on(self, number):
        this = getattr(self, f'spinner{number}')
        this.put(1)
    def off(self, number):
        this = getattr(self, f'spinner{number}')
        this.put(0)
        
    def alloff(self):
        for i in range(1,9):
            self.off(i)
            
