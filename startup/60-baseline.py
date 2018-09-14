
#####################################################################################################
# see https://nsls-ii.github.io/bluesky/tutorial.html#baseline-readings-and-other-supplemental-data #
#####################################################################################################
# see 80-XDI.py for examples of how this is used                                                    #
#####################################################################################################

sd.baseline = [first_crystal.temperature, # relevant DCM temperatures
               compton_shield.temperature,
               xafs_linx,                 # XAFS sample stages
               xafs_liny,
               xafs_lins,
               xafs_linxs,
               xafs_pitch,
               xafs_roll,
               xafs_roth,
               xafs_rotb,
               xafs_rots,
               ring.current,              # other things
]

XDI_record = {'xafs_linx'                  : True,
              'xafs_liny'                  : True,
              'xafs_lins'                  : False,
              'xafs_linxs'                 : False,
              'xafs_pitch'                 : False,
              'xafs_roll'                  : False,
              'xafs_roth'                  : False,
              'xafs_rotb'                  : False,
              'xafs_rots'                  : False,
              'first_crystal_temperature'  : True,
              'compton_shield_temperature' : True,
              'ring_current'               : True,
              }
