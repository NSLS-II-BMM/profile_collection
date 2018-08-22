

def motor_status():
    line = '=' * 78 + '\n'
    text = 'Energy = %.1f   reflection = Si(%s)   mode = %s\n' % (dcm.energy.readback.value, dcm._crystal, dcm.mode)
    text += '\tBragg = %8.5f   2nd Xtal Perp = %7.4f   2nd Xtal Para = %8.4f\n' % \
            (dcm.bragg.user_readback.value, dcm.perp.user_readback.value, dcm.para.user_readback.value)

    text += 'M2\n\tvertical = %7.3f mm\t\tYU  = %7.3f\n' % (m2.vertical.readback.value, m2.yu.user_readback.value)
    text += '\tlateral  = %7.3f mm\t\tYDO = %7.3f\n'     % (m2.lateral.readback.value,  m2.ydo.user_readback.value)
    text += '\tpitch    = %7.3f mrad\t\tYDI = %7.3f\n'   % (m2.pitch.readback.value,    m2.ydi.user_readback.value)
    text += '\troll     = %7.3f mrad\t\tXU  = %7.3f\n'   % (m2.roll.readback.value,     m2.xu.user_readback.value)
    text += '\tyaw      = %7.3f mrad\t\tXD  = %7.3f\n'   % (m2.yaw.readback.value,      m2.xd.user_readback.value)

    stripe = '(Rh/Pt stripe)'
    if m3.xu.user_readback.value < 0:
        stripe = '(Si stripe)'

    text += 'M3  %s\n'                                   % stripe
    text += '\tvertical = %7.3f mm\t\tYU  = %7.3f\n'     % (m3.vertical.readback.value, m3.yu.user_readback.value)
    text += '\tlateral  = %7.3f mm\t\tYDO = %7.3f\n'     % (m3.lateral.readback.value,  m3.ydo.user_readback.value)
    text += '\tpitch    = %7.3f mrad\t\tYDI = %7.3f\n'   % (m3.pitch.readback.value,    m3.ydi.user_readback.value)
    text += '\troll     = %7.3f mrad\t\tXU  = %7.3f\n'   % (m3.roll.readback.value,     m3.xu.user_readback.value)
    text += '\tyaw      = %7.3f mrad\t\tXD  = %7.3f\n'   % (m3.yaw.readback.value,      m3.xd.user_readback.value)

    text += 'Slits3:   vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '\t%7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n' % \
            (slits3.vsize.readback.value, slits3.vcenter.readback.value,
             slits3.hsize.readback.value, slits3.hcenter.readback.value,
             slits3.top.user_readback.value, slits3.bottom.user_readback.value,
             slits3.outboard.user_readback.value, slits3.inboard.user_readback.value)

    text += 'DM3_BCT: %7.3f mm\n' % dm3_bct.user_readback.value

    text += 'XAFS table:\n\tvertical  pitch    roll   YU     YDO     YDI\n'
    text += '\t%7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n' % \
            (xafs_table.vertical.readback.value, xafs_table.pitch.readback.value, xafs_table.roll.readback.value,
             xafs_table.yu.user_readback.value, xafs_table.ydo.user_readback.value, xafs_table.ydi.user_readback.value)

    text += 'XAFS stages:\n'
    text += '\t   linx     liny    roll    pitch    linxs    roth     rotb     rots\n'
    text += '\t%8.3f %8.3f %7.3f %7.3f %8.3f %8.3f %8.3f %8.3f\n' % \
            (xafs_linx.user_readback.value,
             xafs_liny.user_readback.value,
             xafs_roll.user_readback.value,
             xafs_pitch.user_readback.value,
             xafs_linxs.user_readback.value,
             xafs_roth.user_readback.value,
             xafs_rotb.user_readback.value,
             xafs_rots.user_readback.value
            )

    return line + text + line

def ms():
    print(motor_status())
