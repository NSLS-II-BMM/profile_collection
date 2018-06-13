import bluesky as bs
import bluesky.plans as bp
import numpy
import os

# %load /home/bravel/.ipython/profile_collection/startup/99-user_plans.py  
#RE(sample_stack(), DerivedPlot(trans_xmu, xlabel='energy (eV)', ylabel='absorption')) 


def sample_stack():
    dcm.prompt = False
  
    ### sample 1 ############################################################
    yield from mv(xafs_linx, 6.0) # replace linx_current with target X value
    yield from mv(xafs_liny, 67.9) # replace liny_current with target Y value
                                           # replace "sample1" with actual ini file name
    yield from xafs('/home/bravel/commissioning/data/302287/TiSTO40nm.ini')

    ### sample 2 ############################################################
    yield from mv(xafs_linx, 6.0) # replace with sample 2 X, Y, and INI
    yield from mv(xafs_liny, 77.2)
    yield from xafs('/home/bravel/commissioning/data/302287/TiSTO60nm.ini')

    ### sample 3 ############################################################
    yield from mv(xafs_linx, 6.0) # replace with sample 3 X, Y, and INI
    yield from mv(xafs_liny, 87.2)
    yield from xafs('/home/bravel/commissioning/data/302287/TiSTO83nm.ini')
    

    dcm.prompt = True
    
    