

run_report(__file__, text='import more things')

run_report('\tmotor status reporting')
from BMM.motor_status import motor_metadata, motor_status, ms, motor_sidebar, xrd_motors, xrdm

run_report('\tlinescan, rocking curve, slit_height')
from BMM.linescans import linescan

run_report('\tother plans')
from BMM.plans import tu, td, recover_mirror2, recover_mirrors, recover_screens, mvbct, mvrbct, mvbender, mvrbender

run_report('\tchange_mode, change_xtals')
from BMM.modes import change_mode, describe_mode, get_mode, mode, read_mode_data, change_xtals
LOCATION = '/home/xf06bm/git/BMM-beamline-configuration/'
if os.path.isfile(os.path.join(LOCATION, 'Modes.json')):
     MODEDATA = read_mode_data()
if BMMuser.pds_mode is None:
    BMMuser.pds_mode = get_mode()


run_report('\tchange_edge')
from BMM.edge import approximate_pitch, show_edges, change_edge



XDI_record = {'xafs_linx'                        : (True,  'BMM.sample_x_position'),
              'xafs_liny'                        : (True,  'BMM.sample_y_position'),
              'xafs_lins'                        : (False, 'BMM.sample_s_position'),
              'xafs_linxs'                       : (False, 'BMM.sample_ref_position'),
              'xafs_pitch'                       : (False, 'BMM.sample_pitch_position'),
              'xafs_roll'                        : (False, 'BMM.sample_roll_position'),
              'xafs_roth'                        : (False, 'BMM.sample_roth_position'),
              'xafs_wheel'                       : (False, 'BMM.sample_wheel_position'),
              'xafs_ref'                         : (False, 'BMM.sample_ref_position'),
              'xafs_rots'                        : (False, 'BMM.sample_rots_position'),
              'first_crystal_temperature'        : (False, 'BMM.mono_first_crystal_temperature'),
              'compton_shield_temperature'       : (False, 'BMM.mono_compton_shield_temperature'),
              'dm3_bct'                          : (False, 'BMM.beamline_bct_position'),
              'ring_current'                     : (False, 'BMM.facility_ring_current'),
              'bpm_upstream_x'                   : (False, 'BMM.facility_bpm_upstream_x'),
              'bpm_upstream_y'                   : (False, 'BMM.facility_bpm_upstream_y'),
              'bpm_downstream_x'                 : (False, 'BMM.facility_bpm_downstream_x'),
              'bpm_downstream_y'                 : (False, 'BMM.facility_bpm_downstream_y'),
              'monotc_inboard_temperature'       : (False, 'BMM.mono_tc_inboard'),
              'monotc_upstream_high_temperature' : (False, 'BMM.mono_tc_upstream_high'),
              'monotc_downstream_temperature'    : (False, 'BMM.mono_tc_downstream'),
              'monotc_upstream_low_temperature'  : (False, 'BMM.mono_tc_upstream_low'),
              }
run_report('\tXDI')
from BMM.xdi import write_XDI

run_report('\txafs')
from BMM.xafs import howlong, xafs, db2xdi

run_report('\tmono calibration')
from BMM.mono_calibration import calibrate_high_end, calibrate_low_end, calibrate_mono

run_report('\tlarch')
from BMM.larch import Pandrosus, Kekropidai
## examples that only work at BMM...
# se = Pandrosus()
# se.fetch('8e293af3-811c-4e96-a4e5-733d0dc77dad', name='Se metal', mode='transmission')

# seo = Pandrosus()
# seo.fetch('69c35332-6c8a-4f43-9eb2-e5e9cbe7f798', name='SeO2', mode='transmission')

# bunch = Kekropidai(name='Selenium standards')
# bunch.add(se)
# bunch.add(seo)


