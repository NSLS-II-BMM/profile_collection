
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
               dm3_bct,
               ring.current,              # ring current
               bpm_upstream.x,            # BPMs and TCs related to mono stability studies
               bpm_upstream.y,
               bpm_downstream.x,
               bpm_downstream.y,
               monotc_inboard,
               monotc_upstream_high,
               monotc_downstream,
               monotc_upstream_low,
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
              'first_crystal_temperature'  : False,
              'compton_shield_temperature' : False,
              'dm3_bct'                    : False,
              'ring_current'               : False,
              'bpm_upstream_x'             : False,
              'bpm_upstream_y'             : False,
              'bpm_downstream_x'           : False,
              'bpm_downstream_y'           : False,
              'monotc_inboard_temperature' : False,
              'monotc_upstream_high_temperature' : False,
              'monotc_downstream_temperature' : False,
              'monotc_upstream_low_temperature' : False,
              }
