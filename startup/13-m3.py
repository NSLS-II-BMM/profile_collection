run_report(__file__, text='mirror motor definitions and mirror functionality')


from BMM.motors import XAFSEpicsMotor, Mirrors, XAFSTable, GonioTable

## harmonic rejection mirror
m3_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YU}Mtr',   name='m3_yu')
m3_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDO}Mtr',  name='m3_ydo')
m3_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDI}Mtr',  name='m3_ydi')
m3_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XU}Mtr',   name='m3_xu')
m3_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XD}Mtr',   name='m3_xd')
mcs8_motors.extend([m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd])



m1 = Mirrors('XF:06BM-OP{Mir:M1-Ax:',  name='m1', mirror_length=556,  mirror_width=240)
m1.vertical._limits = (-5.0, 5.0)
m1.lateral._limits  = (-5.0, 5.0)
m1.pitch._limits    = (-5.0, 5.0)
m1.roll._limits     = (-5.0, 5.0)
m1.yaw._limits      = (-5.0, 5.0)

m2 = Mirrors('XF:06BMA-OP{Mir:M2-Ax:', name='m2', mirror_length=1288, mirror_width=240)
m2.vertical._limits = (-6.0, 8.0)
m2.lateral._limits  = (-2, 2)
m2.pitch._limits    = (-0.5, 5.0)
m2.roll._limits     = (-2, 2)
m2.yaw._limits      = (-1, 1)

m3 = Mirrors('XF:06BMA-OP{Mir:M3-Ax:', name='m3', mirror_length=667,  mirror_width=240)
m3.vertical._limits = (-11, 1)
m3.lateral._limits  = (-16, 16)
m3.pitch._limits    = (-6, 6)
m3.roll._limits     = (-2, 2)
m3.yaw._limits      = (-1, 1)


def kill_mirror_jacks():
    yield from abs_set(m2_yu.kill_cmd,  1, wait=True)
    #yield from sleep(1)
    yield from abs_set(m2_ydo.kill_cmd, 1, wait=True)
    yield from abs_set(m2_ydi.kill_cmd, 1, wait=True)

    yield from abs_set(m3_yu.kill_cmd,  1, wait=True)
    yield from abs_set(m3_ydo.kill_cmd, 1, wait=True)
    yield from abs_set(m3_ydi.kill_cmd, 1, wait=True)


xt = xafs_table = XAFSTable('XF:06BMA-BI{XAFS-Ax:Tbl_', name='xafs_table', mirror_length=1160,  mirror_width=558)

gonio_table = GonioTable('XF:06BM-ES{SixC-Ax:Tbl_', name='gonio_table', mirror_length=1117.6,  mirror_width=711.12)
