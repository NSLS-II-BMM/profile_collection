import bluesky as bs
import bluesky.plans as bp
import numpy
import os

# %load /home/bravel/.ipython/profile_collection/startup/99-user_plans.py
#RE(sample_stack(), DerivedPlot(trans_xmu, xlabel='energy (eV)', ylabel='absorption'))


from ophyd import EpicsSignal
from bluesky.suspenders import SuspendFloor


def sample_stack():

    #RE.clear_suspenders()
    #sus = SuspendFloor(quadem1.I0, 0.1, resume_thresh=1)
    #RE.install_suspender(sus)
    dcm.prompt = False

    ### sample 1 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 40.2)
    yield from xafs('/home/bravel/commissioning/data/Oxyfluoride/btof.ini')

    ### sample 2 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 20.8)
    yield from xafs('/home/bravel/commissioning/data/Oxyfluoride/Bi2O3.ini')

    ### sample 3 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 1.5)
    yield from xafs('/home/bravel/commissioning/data/Oxyfluoride/BiF3.ini')

    #RE.remove_suspender(sus)
    dcm.prompt = True
