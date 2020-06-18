
#####################################################################################################
# see https://nsls-ii.github.io/bluesky/tutorial.html#baseline-readings-and-other-supplemental-data #
#####################################################################################################
# see 80-XDI.py ~line 123 for examples of how this is used                                          #
#####################################################################################################

# sd.baseline = [first_crystal.temperature, # relevant DCM temperatures
#                compton_shield.temperature,
#                xafs_linx,                 # XAFS sample stages
#                xafs_liny,
#                xafs_lins,
#                xafs_linxs,
#                xafs_pitch,
#                xafs_roll,
#                xafs_roth,
#                xafs_wheel,
#                xafs_rots,
#                bct,
#                #ring.current,              # ring current
#                #bpm_upstream.x,            # BPMs and TCs related to mono stability studies
#                #bpm_upstream.y,
#                #bpm_downstream.x,
#                #bpm_downstream.y,
#                monotc_inboard.temperature,
#                monotc_upstream_high.temperature,
#                monotc_downstream.temperature,
#                monotc_upstream_low.temperature,
# ]

sd.baseline = (xafs_linx, xafs_liny, xafs_pitch, xafs_roll, xafs_linxs, xafs_wheel, xafs_roth, xafs_rots,
               dm3_bct, dm3_foils, dm2_fs,
               slits3.top, slits3.bottom, slits3.outboard, slits3.inboard, slits3.vsize, slits3.vcenter, slits3.hsize, slits3.hcenter, 
               slits2.top, slits2.bottom, slits2.outboard, slits2.inboard, slits2.vsize, slits2.vcenter, slits2.hsize, slits2.hcenter,
               m1.yu, m1.ydo, m1.ydi, m1.xu, m1.xd, m1.vertical, m1.lateral, m1.pitch, m1.roll, m1.yaw,
               m2.yu, m2.ydo, m2.ydi, m2.xu, m2.xd, m2.vertical, m2.lateral, m2.pitch, m2.roll, m2.yaw, m2_bender,
               m3.yu, m3.ydo, m3.ydi, m3.xu, m3.xd, m3.vertical, m3.lateral, m3.pitch, m3.roll, m3.yaw,
               xafs_table.yu, xafs_table.ydo, xafs_table.ydi, xafs_xu , xafs_xd,
               xafs_table.vertical, xafs_table.pitch, xafs_table.roll, 
)



#################################
# XDI_record moved to 80-XDI.py #
#################################

# XDI_record = {'xafs_linx'                        : (True,  'Sample.x_position'),
#               'xafs_liny'                        : (True,  'Sample.y_position'),
#               'xafs_lins'                        : (False, 'Sample.s_position'),
#               'xafs_linxs'                       : (False, 'Sample.ref_position'),
#               'xafs_pitch'                       : (False, 'Sample.pitch_position'),
#               'xafs_roll'                        : (False, 'Sample.roll_position'),
#               'xafs_roth'                        : (False, 'Sample.roth_position'),
#               'xafs_rotb'                        : (True,  'Sample.wheel_position'),
#               'xafs_rots'                        : (False, 'Sample.rots_position'),
#               'first_crystal_temperature'        : (False, 'Mono.first_crystal_temperature'),
#               'compton_shield_temperature'       : (False, 'Mono.compton_shield_temperature'),
#               'dm3_bct'                          : (False, 'Beamline.bct_position'),
#               'ring_current'                     : (False, 'Facility.ring_current'),
#               'bpm_upstream_x'                   : (False, 'Facility.bpm_upstream_x'),
#               'bpm_upstream_y'                   : (False, 'Facility.bpm_upstream_y'),
#               'bpm_downstream_x'                 : (False, 'Facility.bpm_downstream_x'),
#               'bpm_downstream_y'                 : (False, 'Facility.bpm_downstream_y'),
#               'monotc_inboard_temperature'       : (False, 'Mono.tc_inboard'),
#               'monotc_upstream_high_temperature' : (False, 'Mono.tc_upstream_high'),
#               'monotc_downstream_temperature'    : (False, 'Mono.tc_downstream'),
#               'monotc_upstream_low_temperature'  : (False, 'Mono.tc_upstream_low'),
#               }
