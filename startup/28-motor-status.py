
def motor_metadata():
    biglist = (xafs_linx, xafs_liny, xafs_pitch, xafs_roll, xafs_linxs, xafs_wheel, xafs_roth, xafs_rots,
               dm3_bct, dm3_foils, dm2_fs,
               slits3.top, slits3.bottom, slits3.outboard, slits3.inboard, slits3.vsize, slits3.vcenter, slits3.hsize, slits3.hcenter, 
               slits2.top, slits2.bottom, slits2.outboard, slits2.inboard, slits2.vsize, slits2.vcenter, slits2.hsize, slits2.hcenter,
               m1.yu, m1.ydo, m1.ydi, m1.xu, m1.xd, m1.vertical, m1.lateral, m1.pitch, m1.roll, m1.yaw,
               m2.yu, m2.ydo, m2.ydi, m2.xu, m2.xd, m2.vertical, m2.lateral, m2.pitch, m2.roll, m2.yaw, m2_bender,
               m3.yu, m3.ydo, m3.ydi, m3.xu, m3.xd, m3.vertical, m3.lateral, m3.pitch, m3.roll, m3.yaw,
               xafs_table.yu, xafs_table.ydo, xafs_table.ydi, xafs_xu , xafs_xd,
               xafs_table.vertical, xafs_table.pitch, xafs_table.roll, 
           )
    md = dict()
    for m in biglist:
        try:
            md[m.name] = m.readback.value
        except:
            pass
        try:
            md[m.name] = m.user_readback.value
        except:
            pass
    return(md)

def motor_status():
    md = motor_metadata()

    line = ' ' + '=' * 78 + '\n'
    text = '\n Energy = %.1f eV   reflection = Si(%s)   mode = %s\n' % (dcm.energy.readback.value, dcm._crystal, dcm.mode)
    text += '      Bragg = %8.5f   2nd Xtal Perp  = %7.4f   Para = %8.4f\n' % \
            (dcm.bragg.user_readback.value, dcm.perp.user_readback.value, dcm.para.user_readback.value)
    text += '                                  Pitch = %7.4f   Roll = %8.4f\n\n' % \
            (dcm_pitch.user_readback.value, dcm_roll.user_readback.value)

    text += ' M2\n      vertical = %7.3f mm            YU  = %7.3f mm\n' % (md[m2.vertical.name], md[m2.yu.name])
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'      % (md[m2.lateral.name],  md[m2.ydo.name])
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'      % (md[m2.pitch.name],    md[m2.ydi.name])
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'      % (md[m2.roll.name],     md[m2.xu.name])
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n'      % (md[m2.yaw.name],      md[m2.xd.name])
    text += '      bender   = %9.1f steps\n\n'                           %  md[m2_bender.name]

    stripe = '(Rh/Pt stripe)'
    if m3.xu.user_readback.value < 0:
        stripe = '(Si stripe)'

    text += ' M3  %s\n'                                                 % stripe
    text += '      vertical = %7.3f mm            YU  = %7.3f mm\n'     % (md[m3.vertical.name], md[m3.yu.name])
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'     % (md[m3.lateral.name],  md[m3.ydo.name])
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'     % (md[m3.pitch.name],    md[m3.ydi.name])
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'     % (md[m3.roll.name],     md[m3.xu.name])
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n\n'   % (md[m3.yaw.name],      md[m3.xd.name])

    text += ' Slits2:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (md[slits2.vsize.name], md[slits2.vcenter.name],
             md[slits2.hsize.name], md[slits2.hcenter.name],
             md[slits2.top.name], md[slits2.bottom.name],
             md[slits2.outboard.name], md[slits2.inboard.name])

    text += ' Slits3:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (md[slits3.vsize.name], md[slits3.vcenter.name],
             md[slits3.hsize.name], md[slits3.hcenter.name],
             md[slits3.top.name], md[slits3.bottom.name],
             md[slits3.outboard.name], md[slits3.inboard.name])

    text += ' DM3_BCT: %7.3f mm      '   % md[dm3_bct.name]
    text += ' DM3_foils: %7.3f mm      ' % md[dm3_foils.name]
    text += ' DM2_fs: %7.3f mm\n\n'      % md[dm2_fs.name]

    text += ' XAFS table:\n      vertical  pitch    roll   YU     YDO     YDI\n'
    text += '       %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n\n' % \
            (md[xafs_table.vertical.name], md[xafs_table.pitch.name], md[xafs_table.roll.name],
             md[xafs_table.yu.name], md[xafs_table.ydo.name], md[xafs_table.ydi.name])

    text += ' XAFS stages (motor names are xafs_<name>, units mm or deg):\n'
    text += '     name =     x        y     roll    pitch    linxs    roth     wheel    rots\n'
    text += '           %8.3f %8.3f %7.3f %7.3f %8.3f %8.3f %8.3f %8.3f\n' % \
            (md[xafs_linx.name],
             md[xafs_liny.name],
             md[xafs_roll.name],
             md[xafs_pitch.name],
             md[xafs_linxs.name],
             md[xafs_roth.name],
             md[xafs_rotb.name],
             md[xafs_rots.name]
            )

    return text
    # return line + text + line

def ms():
    boxedtext('BMM motor status', motor_status(), 'cyan', width=84)


def motor_sidebar(md=None):
    '''
    Generate a list of motor positions to be used in the static html page for a scan sequence.
    Return value is a long string with html tags and entities embedded in the string.
    '''
    if md is None or type(md) is not dict:
        md = motor_metadata()
    motors = ''
        
    mlist = []
    mlist.append('XAFS stages (motor names are xafs_*):')
    mlist.append('x = %.3f ; y = %.3f'         % (md[xafs_linx.name],  md[xafs_liny.name]))
    mlist.append('pitch = %.3f ; roll = %.3f'  % (md[xafs_pitch.name], md[xafs_roll.name]))
    mlist.append('ref = %.3f ; wheel = %.3f'   % (md[xafs_linxs.name], md[xafs_wheel.name]))
    mlist.append('roth = %.3f ; rots = %.3f'   % (md[xafs_roth.name],  md[xafs_rots.name]))
    mlist.append('wheel slot = %2d'            % xafs_wheel.current_slot())
    motors += '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>DM3_BCT: %.3f mm' % md[dm3_bct.name]

    mlist = []
    mlist.append('Slits3:')
    mlist.append('vsize = %.3f ; vcenter =%.3f'      % (md[slits3.vsize.name],    md[slits3.vcenter.name]))
    mlist.append('hsize = %.3f ; hcenter =%.3f'      % (md[slits3.hsize.name],    md[slits3.hcenter.name]))
    mlist.append('top  = %.3f ; bottom = %.3f'       % (md[slits3.top.name],      md[slits3.bottom.name]))
    mlist.append('outboard  = %.3f ; inboard = %.3f' % (md[slits3.outboard.name], md[slits3.inboard.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('M2')
    mlist.append('vertical = %.3f mm ; YU  = %.3f mm'   % (md[m2.vertical.name], md[m2.yu.name]))
    mlist.append('lateral  = %.3f mm ; YDO = %.3f mm'   % (md[m2.lateral.name],  md[m2.ydo.name]))
    mlist.append('pitch    = %.3f mrad ; YDI = %.3f mm' % (md[m2.pitch.name],    md[m2.ydi.name]))
    mlist.append('roll     = %.3f mrad ; XU  = %.3f mm' % (md[m2.roll.name],     md[m2.xu.name]))
    mlist.append('yaw      = %.3f mrad ; XD  = %.3f mm' % (md[m2.yaw.name],      md[m2.xd.name]))
    mlist.append('bender   = %9.1f steps'               %  md[m2_bender.name])
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)


    mlist = []
    stripe = '(Rh/Pt stripe)'
    if md[m3.xu.name] < 0:
        stripe = '(Si stripe)'
    mlist.append('M3  %s' % stripe)
    mlist.append('vertical = %.3f  mm ; YU  = %.3f mm'   % (md[m3.vertical.name], md[m3.yu.name]))
    mlist.append('lateral  = %.3f  mm ; YDO = %.3f mm'   % (md[m3.lateral.name],  md[m3.ydo.name]))
    mlist.append('pitch    = %.3f  mrad ; YDI = %.3f mm' % (md[m3.pitch.name],    md[m3.ydi.name]))
    mlist.append('roll     = %.3f  mrad ; XU  = %.3f mm' % (md[m3.roll.name],     md[m3.xu.name]))
    mlist.append('yaw      = %.3f  mrad ; XD  = %.3f mm' % (md[m3.yaw.name],      md[m3.xd.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('XAFS table:')
    mlist.append('vertical = %.3f ; YU = %.3f' % (md[xafs_table.vertical.name], md[xafs_table.yu.name]))
    mlist.append('pitch = %.3f ; YDO = %.3f'   % (md[xafs_table.pitch.name],    md[xafs_table.ydo.name]))
    mlist.append('roll = %.3f ; YDI = %.3f'    % (md[xafs_table.roll.name],     md[xafs_table.ydi.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('Slits2:')
    mlist.append('vsize = %.3f ; vcenter =%.3f'      % (md[slits2.vsize.name],    md[slits2.vcenter.name]))
    mlist.append('hsize = %.3f ; hcenter =%.3f'      % (md[slits2.hsize.name],    md[slits2.hcenter.name]))
    mlist.append('top  = %.3f ; bottom = %.3f'       % (md[slits2.top.name],      md[slits2.bottom.name]))
    mlist.append('outboard  = %.3f ; inboard = %.3f' % (md[slits2.outboard.name], md[slits2.inboard.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>DM3_foils: %.3f mm' % md[dm3_foils.name]
    motors += '\n<br>DM2_foils: %.3f mm' % md[dm2_fs.name]

    
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
