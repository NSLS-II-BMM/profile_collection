from ophyd import EpicsMotor, EpicsSignalRO

run_report(__file__, text='most motor definitions')

from BMM.motors import FMBOEpicsMotor, XAFSEpicsMotor, VacuumEpicsMotor, EndStationEpicsMotor


mcs8_motors = list()

## front end slits
fe_slits_horizontal1 = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Hrz}Mtr',      name='fe_slits_horizontal1')
fe_slits_incline1    = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Inc}Mtr',      name='fe_slits_incline1')
fe_slits_o           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:O}Mtr',        name='fe_slits_o')
fe_slits_t           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:T}Mtr',        name='fe_slits_t')
fe_slits_horizontal2 = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Hrz}Mtr',      name='fe_slits_horizontal2')
fe_slits_incline2    = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Inc}Mtr',      name='fe_slits_incline2')
fe_slits_i           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:I}Mtr',        name='fe_slits_i')
fe_slits_b           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:B}Mtr',        name='fe_slits_b')
fe_slits_hsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}size',   name='fe_slits_hsize')
fe_slits_vsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}size',   name='fe_slits_vsize')
fe_slits_hcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}center', name='fe_slits_hcenter')
fe_slits_vcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}center', name='fe_slits_vcenter')

    
## collimating mirror
m1_yu     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YU}Mtr',   name='m1_yu')
m1_ydo    = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YDO}Mtr',  name='m1_ydo')
m1_ydi    = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YDI}Mtr',  name='m1_ydi')
m1_xu     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:XU}Mtr',   name='m1_xu')
m1_xd     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:XD}Mtr',   name='m1_xd')
mcs8_motors.extend([m1_yu, m1_ydo, m1_ydi, m1_xu, m1_xd])

## DM1
dm1_filters1 = XAFSEpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y1}Mtr', name='dm1_filters1')
dm1_filters2 = XAFSEpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y2}Mtr', name='dm1_filters2')
mcs8_motors.extend([dm1_filters1, dm1_filters2])
dm1_filters2.llm.put(-52)


## monochromator
dcm_bragg = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Bragg}Mtr', name='dcm_bragg')
dcm_pitch = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:P2}Mtr',    name='dcm_pitch')
dcm_roll  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:R2}Mtr',    name='dcm_roll')
dcm_perp  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Per2}Mtr',  name='dcm_perp')
dcm_para  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Par2}Mtr',  name='dcm_para')
dcm_x     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:X}Mtr',     name='dcm_x')
dcm_y     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Y}Mtr',     name='dcm_y')
mcs8_motors.extend([dcm_bragg, dcm_pitch, dcm_roll, dcm_perp,
                   dcm_para, dcm_x, dcm_y])

dcm_para.hlm.put(161)        # this is 21200 on the Si(111) mono
#                            # hard limit is at 162.48

dcm_bragg.encoder.kind = 'hinted'
dcm_bragg.user_readback.kind = 'hinted'
dcm_bragg.user_setpoint.kind = 'normal'
dcm_bragg.velocity.put(0.3)
dcm_bragg.acceleration.put(BMMuser.acc_fast)

## for some reason, this needs to be set explicitly
dcm_x.hlm.put(68)
dcm_x.llm.put(0)
dcm_x.velocity.put(0.6)

## this is about as fast as this motor can go, 1.25 results in a following error
dcm_para.velocity.put(0.2)
dcm_para.hvel_sp.put(0.2)
dcm_perp.velocity.put(0.2)
dcm_perp.hvel_sp.put(0.2)

## focusing mirror
m2_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YU}Mtr',   name='m2_yu')
m2_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDO}Mtr',  name='m2_ydo')
m2_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDI}Mtr',  name='m2_ydi')
m2_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XU}Mtr',   name='m2_xu')
m2_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XD}Mtr',   name='m2_yxd')
m2_bender = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:Bend}Mtr', name='m2_bender')
mcs8_motors.extend([m2_yu, m2_ydo, m2_ydi, m2_xu, m2_xd, m2_bender])
m2_xu.velocity.put(0.05)
m2_xd.velocity.put(0.05)

## DM2
dm2_slits_o = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:O}Mtr',  name='dm2_slits_o')
dm2_slits_i = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:I}Mtr',  name='dm2_slits_i')
dm2_slits_t = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:T}Mtr',  name='dm2_slits_o')
dm2_slits_b = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:B}Mtr',  name='dm2_slits_b')
dm2_fs      = XAFSEpicsMotor('XF:06BMA-BI{Diag:02-Ax:Y}Mtr', name='dm2_fs')
mcs8_motors.extend([dm2_slits_o, dm2_slits_i, dm2_slits_t, dm2_slits_b, dm2_fs])
#dm2_fs.wait_for_connection()
dm2_fs.hvel_sp.put(0.0005)

## DM3
dm3_fs      = XAFSEpicsMotor('XF:06BM-BI{FS:03-Ax:Y}Mtr',   name='dm3_fs')
dm3_foils   = XAFSEpicsMotor('XF:06BM-BI{Fltr:01-Ax:Y}Mtr', name='dm3_foils')
dm3_bct     = XAFSEpicsMotor('XF:06BM-BI{BCT-Ax:Y}Mtr',     name='dm3_bct')
dm3_bpm     = XAFSEpicsMotor('XF:06BM-BI{BPM:1-Ax:Y}Mtr',   name='dm3_bpm')
dm3_slits_o = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:O}Mtr',  name='dm3_slits_o')
dm3_slits_i = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:I}Mtr',  name='dm3_slits_i')
dm3_slits_t = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:T}Mtr',  name='dm3_slits_t')
dm3_slits_b = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:B}Mtr',  name='dm3_slits_b')
mcs8_motors.extend([dm3_slits_o, dm3_slits_i, dm3_slits_t, dm3_slits_b,
                    dm3_fs, dm3_foils, dm3_bct, dm3_bpm])

dm3_slits_i.user_offset.put(-6.9181)
dm3_slits_o.user_offset.put(7.087)


dm3_fs.llm.value = -65
dm3_bct.velocity.put(0.4)
dm3_bct.acceleration.put(0.25)
dm3_bct.hvel_sp.put(0.05)


#bct = EpicsMotor('XF:06BM-BI{BCT-Ax:Y}Mtr', name='dm3bct')

## XAFS table
xafs_yu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YU}Mtr',  name='xafs_yu')
xafs_ydo = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDO}Mtr', name='xafs_ydo')
xafs_ydi = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDI}Mtr', name='xafs_ydi')
xafs_xu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XU}Mtr',  name='xafs_xu')
xafs_xd  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XD}Mtr',  name='xafs_xd')



## XAFS stages
#xafs_wheel = xafs_rotb  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_roth  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotH}Mtr',  name='xafs_roth')
xafs_rots  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotS}Mtr',  name='xafs_rots')
xafs_lins  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinS}Mtr',  name='xafs_lins')
xafs_linxs = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinXS}Mtr', name='xafs_linxs')
xafs_x     = xafs_linx  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinX}Mtr',  name='xafs_linx')
xafs_y     = xafs_liny  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinY}Mtr',  name='xafs_liny')
xafs_roll  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Pitch}Mtr', name='xafs_roll') # note: the way this stage gets mounted, the
xafs_pitch = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Roll}Mtr',  name='xafs_pitch') # EPICS names are swapped.  sigh....

xafs_garot = xafs_mtr8  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Mtr8}Mtr',  name='xafs_mtr8') # EPICS names are swapped. 
xafs_garot.user_offset.put(179.47455)

xafs_linxs._limits = (-95, 95)
xafs_linxs.user_offset.put(102)
xafs_linx.kill_cmd.kind = 'config'

# RE(scan(dets, m3.pitch, -4, -3, num=10))

xafs_x.default_llm = 2
xafs_x.default_hlm = 126
xafs_y.default_llm = 10
xafs_y.default_hlm = 200


def homed():
    for m in mcs8_motors:
        if m.hocpl.get():
            print("%-12s : %s" % (m.name, m.hocpl.enum_strs[m.hocpl.get()]))
        else:
            print("%-12s : %s" % (m.name, error_msg(m.hocpl.enum_strs[m.hocpl.get()])))

def ampen():
    for m in mcs8_motors:
        if m.ampen.get():
            print("%-12s : %s" % (m.name, warning_msg(m.ampen.enum_strs[m.ampen.get()])))
        else:
            print("%-12s : %s" % (m.name, m.ampen.enum_strs[m.ampen.get()]))
            

def amfe():
    print(bold_msg("%-12s : %s / %s" % ('motor', 'AMFE', 'AMFAE')))
    for m in mcs8_motors:
        if m.amfe.get():
            fe  = warning_msg(m.amfe.enum_strs[m.amfe.get()])
        else:
            fe  = m.amfe.enum_strs[m.amfe.get()]
        if m.amfae.get():
            fae = warning_msg(m.amfae.enum_strs[m.amfae.get()])
        else:
            fae = m.amfae.enum_strs[m.amfae.get()]
        print("%-12s : %s / %s" % (m.name, fe, fae))
faults = amfe
            


xrd_delta  = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:VTTH}Mtr',    name='delta')
xrd_eta    = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:VTH}Mtr',     name='eta')
xrd_chi    = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:CHI}Mtr',     name='chi')
xrd_phi    = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:PHI}Mtr',     name='phi')
xrd_mu     = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:HTH}Mtr',     name='mu')
xrd_nu     = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:HTTH}Mtr',    name='nu')

xrd_anal   = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:ANAL}Mtr',    name='analyzer')
xrd_det    = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:DET}Mtr',     name='detector')
xrd_dethor = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:DETHOR}Mtr',  name='detector horizontal')

xrd_wheel1 = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:WHEEL1}Mtr',  name='wheel1')
xrd_wheel2 = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:WHEEL2}Mtr',  name='wheel2')

xrd_samx   = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:SAMX}Mtr',    name='sample x')
xrd_samy   = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:SAMY}Mtr',    name='sample y')
xrd_samz   = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:SAMZ}Mtr',    name='sample z')

xrd_tabyd  = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_YD}Mtr',  name='table y downstream')
xrd_tabyui = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_YUI}Mtr', name='table y upstream inboard')
xrd_tabyuo = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_YUO}Mtr', name='table y upstream outboard')
xrd_tabxu  = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_XU}Mtr',  name='table x upstream')
xrd_tabxd  = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_XD}Mtr',  name='table x downstream')
xrd_tabz   = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Tbl_Z}Mtr',   name='table z')

xrd_slit1t = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Slt1_T}Mtr',  name='slit 1 top')
xrd_slit1b = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Slt1_B}Mtr',  name='slit 1 bottom')
xrd_slit1i = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Slt1_I}Mtr',  name='slit 1 inboard')
xrd_slit1o = EndStationEpicsMotor('XF:06BM-ES{SixC-Ax:Slt1_O}Mtr',  name='slit 1 outboard')
