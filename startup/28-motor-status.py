

def motor_status():
    line = ' ' + '=' * 78 + '\n'
    text = '\n Energy = %.1f eV   reflection = Si(%s)   mode = %s\n' % (dcm.energy.readback.value, dcm._crystal, dcm.mode)
    text += '      Bragg = %8.5f   2nd Xtal Perp  = %7.4f   Para = %8.4f\n' % \
            (dcm.bragg.user_readback.value, dcm.perp.user_readback.value, dcm.para.user_readback.value)
    text += '                                  Pitch = %7.4f   Roll = %8.4f\n\n' % \
            (dcm_pitch.user_readback.value, dcm_roll.user_readback.value)

    text += ' M2\n      vertical = %7.3f mm            YU  = %7.3f mm\n' % (m2.vertical.readback.value, m2.yu.user_readback.value)
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'      % (m2.lateral.readback.value,  m2.ydo.user_readback.value)
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'      % (m2.pitch.readback.value,    m2.ydi.user_readback.value)
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'      % (m2.roll.readback.value,     m2.xu.user_readback.value)
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n'      % (m2.yaw.readback.value,      m2.xd.user_readback.value)
    text += '      bender   = %9.1f steps\n\n'                           %  m2_bender.user_readback.value

    stripe = '(Rh/Pt stripe)'
    if m3.xu.user_readback.value < 0:
        stripe = '(Si stripe)'

    text += ' M3  %s\n'                                                 % stripe
    text += '      vertical = %7.3f mm            YU  = %7.3f mm\n'     % (m3.vertical.readback.value, m3.yu.user_readback.value)
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'     % (m3.lateral.readback.value,  m3.ydo.user_readback.value)
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'     % (m3.pitch.readback.value,    m3.ydi.user_readback.value)
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'     % (m3.roll.readback.value,     m3.xu.user_readback.value)
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n\n'   % (m3.yaw.readback.value,      m3.xd.user_readback.value)

    text += ' Slits2:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (slits2.vsize.readback.value, slits2.vcenter.readback.value,
             slits2.hsize.readback.value, slits2.hcenter.readback.value,
             slits2.top.user_readback.value, slits2.bottom.user_readback.value,
             slits2.outboard.user_readback.value, slits2.inboard.user_readback.value)

    text += ' Slits3:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (slits3.vsize.readback.value, slits3.vcenter.readback.value,
             slits3.hsize.readback.value, slits3.hcenter.readback.value,
             slits3.top.user_readback.value, slits3.bottom.user_readback.value,
             slits3.outboard.user_readback.value, slits3.inboard.user_readback.value)

    text += ' DM3_BCT: %7.3f mm\t' % dm3_bct.user_readback.value
    text += ' DM3_foils: %7.3f mm\t' % dm3_foils.user_readback.value
    text += ' DM2_fs: %7.3f mm\n\n' % dm2_fs.user_readback.value

    text += ' XAFS table:\n      vertical  pitch    roll   YU     YDO     YDI\n'
    text += '       %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n\n' % \
            (xafs_table.vertical.readback.value, xafs_table.pitch.readback.value, xafs_table.roll.readback.value,
             xafs_table.yu.user_readback.value, xafs_table.ydo.user_readback.value, xafs_table.ydi.user_readback.value)

    text += ' XAFS stages (motor names are xafs_<name>, units mm or deg):\n'
    text += '     name =     x        y     roll    pitch    linxs    roth     wheel    rots\n'
    text += '           %8.3f %8.3f %7.3f %7.3f %8.3f %8.3f %8.3f %8.3f\n' % \
            (xafs_linx.user_readback.value,
             xafs_liny.user_readback.value,
             xafs_roll.user_readback.value,
             xafs_pitch.user_readback.value,
             xafs_linxs.user_readback.value,
             xafs_roth.user_readback.value,
             xafs_rotb.user_readback.value,
             xafs_rots.user_readback.value
            )

    return text
    # return line + text + line

def ms():
    boxedtext('BMM motor status', motor_status(), 'cyan', width=84)


def motor_sidebar():
    '''
    Generate a list of motor positions to be used in the static html page for a scan sequence.
    Return value is a long string with html tags and entities embedded in the string.
    '''
    motors = ''
        
    mlist = []
    mlist.append('XAFS stages (motor names are xafs_*):')
    mlist.append('x = %.3f ; y = %.3f'         % (xafs_linx.user_readback.value,  xafs_liny.user_readback.value))
    mlist.append('pitch = %.3f ; roll = %.3f'  % (xafs_pitch.user_readback.value, xafs_roll.user_readback.value))
    mlist.append('ref = %.3f ; wheel = %.3f'   % (xafs_linxs.user_readback.value, xafs_wheel.user_readback.value))
    mlist.append('roth = %.3f ; rots = %.3f'   % (xafs_roth.user_readback.value,  xafs_rots.user_readback.value))
    mlist.append('wheel slot = %2d'            % xafs_wheel.current_slot())
    motors += '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>DM3_BCT: %.3f mm' % dm3_bct.user_readback.value

    mlist = []
    mlist.append('Slits3:')
    mlist.append('vsize = %.3f ; vcenter =%.3f'      % (slits3.vsize.readback.value,         slits3.vcenter.readback.value))
    mlist.append('hsize = %.3f ; hcenter =%.3f'      % (slits3.hsize.readback.value,         slits3.hcenter.readback.value))
    mlist.append('top  = %.3f ; bottom = %.3f'       % (slits3.top.user_readback.value,      slits3.bottom.user_readback.value))
    mlist.append('outboard  = %.3f ; inboard = %.3f' % (slits3.outboard.user_readback.value, slits3.inboard.user_readback.value))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('M2')
    mlist.append('vertical = %.3f mm ; YU  = %.3f mm'   % (m2.vertical.readback.value, m2.yu.user_readback.value))
    mlist.append('lateral  = %.3f mm ; YDO = %.3f mm'   % (m2.lateral.readback.value,  m2.ydo.user_readback.value))
    mlist.append('pitch    = %.3f mrad ; YDI = %.3f mm' % (m2.pitch.readback.value,    m2.ydi.user_readback.value))
    mlist.append('roll     = %.3f mrad ; XU  = %.3f mm' % (m2.roll.readback.value,     m2.xu.user_readback.value))
    mlist.append('yaw      = %.3f mrad ; XD  = %.3f mm' % (m2.yaw.readback.value,      m2.xd.user_readback.value))
    mlist.append('bender   = %9.1f steps'               %  m2_bender.user_readback.value)
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)


    mlist = []
    stripe = '(Rh/Pt stripe)'
    if m3.xu.user_readback.value < 0:
        stripe = '(Si stripe)'
    mlist.append('M3  %s' % stripe)
    mlist.append('vertical = %.3f  mm ; YU  = %.3f mm'   % (m3.vertical.readback.value, m3.yu.user_readback.value))
    mlist.append('lateral  = %.3f  mm ; YDO = %.3f mm'   % (m3.lateral.readback.value,  m3.ydo.user_readback.value))
    mlist.append('pitch    = %.3f  mrad ; YDI = %.3f mm' % (m3.pitch.readback.value,    m3.ydi.user_readback.value))
    mlist.append('roll     = %.3f  mrad ; XU  = %.3f mm' % (m3.roll.readback.value,     m3.xu.user_readback.value))
    mlist.append('yaw      = %.3f  mrad ; XD  = %.3f mm' % (m3.yaw.readback.value,      m3.xd.user_readback.value))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('XAFS table:')
    mlist.append('vertical = %.3f ; YU = %.3f' % (xafs_table.vertical.readback.value, xafs_table.yu.user_readback.value))
    mlist.append('pitch = %.3f ; YDO = %.3f'   % (xafs_table.pitch.readback.value,    xafs_table.ydo.user_readback.value))
    mlist.append('roll = %.3f ; YDI = %.3f'    % (xafs_table.roll.readback.value,     xafs_table.ydi.user_readback.value))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('Slits2:')
    mlist.append('vsize = %.3f ; vcenter =%.3f'      % (slits2.vsize.readback.value,         slits2.vcenter.readback.value))
    mlist.append('hsize = %.3f ; hcenter =%.3f'      % (slits2.hsize.readback.value,         slits2.hcenter.readback.value))
    mlist.append('top  = %.3f ; bottom = %.3f'       % (slits2.top.user_readback.value,      slits2.bottom.user_readback.value))
    mlist.append('outboard  = %.3f ; inboard = %.3f' % (slits2.outboard.user_readback.value, slits2.inboard.user_readback.value))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>DM3_foils: %.3f mm' % dm3_foils.user_readback.value
    motors += '\n<br>DM2_foils: %.3f mm' % dm2_fs.user_readback.value

    
    return motors


def xrd_motors():
    text = '\n'
    for m in (xrd_delta,  xrd_eta,    xrd_chi,    xrd_phi,    xrd_mu,     xrd_nu,
              xrd_anal,   xrd_det,    xrd_dethor, xrd_wheel1, xrd_wheel2,
              xrd_samx,   xrd_samy,   xrd_samz,   xrd_tabyd,  xrd_tabyui,
              xrd_tabyuo, xrd_tabxu,  xrd_tabxd,  xrd_tabz,   xrd_slit1t,
              xrd_slit1b, xrd_slit1i, xrd_slit1o):
        text += '  %-26s: %8.3f %s\n' % (m.name, m.user_readback.value, m.describe()[m.name]['units'])
    return text

def xrdm():
    boxedtext('XRD motor status', xrd_motors(), 'cyan', width=60)
