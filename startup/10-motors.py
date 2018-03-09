from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

## monochromator
dcm_bragg = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Bragg}Mtr', name='dcm_bragg')
dcm_pitch = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:P2}Mtr',    name='dcm_pitch')
dcm_roll  = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:R2}Mtr',    name='dcm_roll')
dcm_perp  = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Per2}Mtr',  name='dcm_perp')
dcm_para  = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Par2}Mtr',  name='dcm_para')
dcm_x     = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:X}Mtr',     name='dcm_x')
dcm_y     = EpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Y}Mtr',     name='dcm_y')

## collimating mirror
m1_yu     = EpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YU}Mtr',   name='m1_yu')
m1_ydo    = EpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YDO}Mtr',  name='m1_ydo')
m1_ydi    = EpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YDI}Mtr',  name='m1_ydi')
m1_xu     = EpicsMotor('XF:06BMA-OP{Mir:M1-Ax:XU}Mtr',   name='m1_xu')
m1_xd     = EpicsMotor('XF:06BMA-OP{Mir:M1-Ax:XD}Mtr',   name='m1_yxd')

## focusing mirror
m2_yu     = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YU}Mtr',   name='m2_yu')
m2_ydo    = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDO}Mtr',  name='m2_ydo')
m2_ydi    = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDI}Mtr',  name='m2_ydi')
m2_xu     = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XU}Mtr',   name='m2_xu')
m2_xd     = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XD}Mtr',   name='m2_yxd')
m2_bender = EpicsMotor('XF:06BMA-OP{Mir:M2-Ax:Bend}Mtr', name='m2_bender')

## front end slits
fe_slits_horizontal1 = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Hrz}Mtr', name='fe_slits_horizontal1')
fe_slits_incline1    = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Inc}Mtr', name='fe_slits_incline1')
fe_slits_o           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:O}Mtr',   name='fe_slits_o')
fe_slits_t           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:T}Mtr',   name='fe_slits_t')
fe_slits_horizontal2 = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Hrz}Mtr', name='fe_slits_horizontal2')
fe_slits_incline2    = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Inc}Mtr', name='fe_slits_incline2')
fe_slits_i           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:I}Mtr',   name='fe_slits_i')
fe_slits_b           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:B}Mtr',   name='fe_slits_b')
fe_slits_hsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}size', name='fe_slits_hsize')
fe_slits_vsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}size', name='fe_slits_vsize')
fe_slits_hcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}center', name='fe_slits_hcenter')
fe_slits_vcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}center', name='fe_slits_vcenter')

## DM1
dm1_filters1 = EpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y1}Mtr', name='dm1_filters1')
dm1_filters2 = EpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y2}Mtr', name='dm1_filters2')

## DM2
dm2_slits_o = EpicsMotor('XF:06BMA-OP{Slt:01-Ax:O}Mtr', name='dm2_slits_o')
dm2_slits_i = EpicsMotor('XF:06BMA-OP{Slt:01-Ax:I}Mtr', name='dm2_slits_i')
dm2_slits_t = EpicsMotor('XF:06BMA-OP{Slt:01-Ax:T}Mtr', name='dm2_slits_o')
dm2_slits_b = EpicsMotor('XF:06BMA-OP{Slt:01-Ax:B}Mtr', name='dm2_slits_b')
dm2_fs = EpicsMotor('XF:06BMA-BI{Diag:02-Ax:Y}Mtr', name='dm2_fs')

## DM3
dm3_fs      = EpicsMotor('XF:06BM-BI{FS:03-Ax:Y}Mtr',   name='dm3_fs')
dm3_foils   = EpicsMotor('XF:06BM-BI{Fltr:01-Ax:Y}Mtr', name='dm3_foils')
dm3_bct     = EpicsMotor('XF:06BM-BI{BCT-Ax:Y}Mtr',     name='dm3_bct')
dm3_bpm     = EpicsMotor('XF:06BM-BI{BPM:1-Ax:Y}Mtr',   name='dm3_bpm')
dm3_slits_o = EpicsMotor('XF:06BM-BI{Slt:02-Ax:O}Mtr',  name='dm2_slits_o')
dm3_slits_i = EpicsMotor('XF:06BM-BI{Slt:02-Ax:I}Mtr',  name='dm2_slits_i')
dm3_slits_t = EpicsMotor('XF:06BM-BI{Slt:02-Ax:T}Mtr',  name='dm2_slits_t')
dm3_slits_b = EpicsMotor('XF:06BM-BI{Slt:02-Ax:B}Mtr',  name='dm2_slits_b')

## XAFS table
xafs_yu  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YU}Mtr',  name='xafs_yu')
xafs_ydo = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDO}Mtr', name='xafs_ydo')
xafs_ydi = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDI}Mtr', name='xafs_ydi')
xafs_xu  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XU}Mtr',  name='xafs_xu')
xafs_xd  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XD}Mtr',  name='xafs_xd')

## XAFS stages
xafs_rotb  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_rotb')
xafs_roth  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:RotH}Mtr',  name='xafs_roth')
xafs_rots  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:RotS}Mtr',  name='xafs_rots')
xafs_lins  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:LinS}Mtr',  name='xafs_lins')
xafs_linxs = EpicsMotor('XF:06BMA-BI{XAFS-Ax:LinXS}Mtr', name='xafs_linxs')
xafs_linx  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:LinX}Mtr',  name='xafs_linx')
xafs_liny  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:LinY}Mtr',  name='xafs_liny')
xafs_pitch = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Pitch}Mtr', name='xafs_pitch')
xafs_roll  = EpicsMotor('XF:06BMA-BI{XAFS-Ax:Roll}Mtr',  name='xafs_roll')



# RE(scan(dets, m3.pitch, -4, -3, num=10))
