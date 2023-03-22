from ophyd import EpicsSignal

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

def set_desc_strings():
    '''A bunch of motors have .DESC that are set weirdly in their IOC
    configuration files.  The configuration could be edited, for sure.
    But that field is a read/write PV, so it is a fixable problem at
    the bsui level.  The point is to have sensible strings displayed
    on CSS screens.

    '''
    
    ## focusing mirror
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:YU}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - YU')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:YDO}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - YDO')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:YDI}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - YDI')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:XU}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - XU')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:XD}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - XD')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M2-Ax:Bend}Mtr.DESC', name='toss')
    toss.put('Mir:M2 - Bender')

    ## harmonic rejection mirror
    toss = EpicsSignal('XF:06BMA-OP{Mir:M3-Ax:YU}Mtr.DESC', name='toss')
    toss.put('Mir:M3 - YU')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M3-Ax:YDO}Mtr.DESC', name='toss')
    toss.put('Mir:M3 - YDO')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M3-Ax:YDI}Mtr.DESC', name='toss')
    toss.put('Mir:M3 - YDI')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M3-Ax:XU}Mtr.DESC', name='toss')
    toss.put('Mir:M3 - XU')
    toss = EpicsSignal('XF:06BMA-OP{Mir:M3-Ax:XD}Mtr.DESC', name='toss')
    toss.put('Mir:M3 - XD')

    toss = EpicsSignal('XF:06BMA-OP{Slt:01-Ax:O}Mtr.DESC', name='toss')
    toss.put('Slit2 outboard')
    toss = EpicsSignal('XF:06BMA-OP{Slt:01-Ax:I}Mtr.DESC', name='toss')
    toss.put('Slit2 inboard')
    toss = EpicsSignal('XF:06BMA-OP{Slt:01-Ax:T}Mtr.DESC', name='toss')
    toss.put('Slit2 top')
    toss = EpicsSignal('XF:06BMA-OP{Slt:01-Ax:B}Mtr.DESC', name='toss')
    toss.put('Slit2 bottom')
    
    toss = EpicsSignal('XF:06BM-BI{Slt:02-Ax:O}Mtr.DESC', name='toss')
    toss.put('Slit3 outboard')
    toss = EpicsSignal('XF:06BM-BI{Slt:02-Ax:I}Mtr.DESC', name='toss')
    toss.put('Slit3 inboard')
    toss = EpicsSignal('XF:06BM-BI{Slt:02-Ax:T}Mtr.DESC', name='toss')
    toss.put('Slit3 top')
    toss = EpicsSignal('XF:06BM-BI{Slt:02-Ax:B}Mtr.DESC', name='toss')
    toss.put('Slit3 bottom')
    

    ## most of these are motors that have been repurposed and so are used in bsui by different names.
    ## pitch and roll are confusing.  those two were defined in the wrong orientation way back when,
    ## so they got swapped in bsui.  that means that XF:06BMA-BI{XAFS-Ax:Roll}Mtr is used for the pitch
    ## direction and same for the other direction.  just awful and should be fixed in the IOC
    for s in ('xafs_mtr8', 'xafs_linxs', 'xafs_rotb', 'xafs_linx', 'xafs_liny', 'xafs_lins', 'xafs_pitch', 'xafs_roll'):
        m = user_ns[s]
        toss = EpicsSignal(f'{m.prefix}.DESC', name = 'toss')
        toss.put(m.name)
