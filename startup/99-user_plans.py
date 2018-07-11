import bluesky as bs
import bluesky.plans as bp
import numpy
import os

#############################################################################
# %run -i /home/bravel/.ipython/profile_collection/startup/99-user_plans.py #
# RE(sample_stack())                                                        #
#############################################################################

def sample_stack():

    BMM_xsp.prompt = False

    ### sample 1 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 40.2)
    yield from xafs('/home/bravel/BMM_data/bucket/scan.ini')

    ### sample 2 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 20.8)
    yield from xafs('/home/bravel/BMM_data/bucket/scan.ini', filename='Bi2O3', sample='Bi2O3')

    ### sample 3 ############################################################
    yield from mv(xafs_linx, -114.3, xafs_liny, 1.5)
    yield from xafs('/home/bravel/BMM_data/bucket/scan.ini', filename='BiF3', sample='BiF3', nscans=4)

    BMM_xsp.prompt = True
