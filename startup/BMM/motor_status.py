
from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.functions import boxedtext

def motor_metadata(uid=None):
    biglist = (user_ns['xafs_linx'], user_ns['xafs_liny'], user_ns['xafs_pitch'], user_ns['xafs_roll'],
               user_ns['xafs_linxs'], user_ns['xafs_wheel'], user_ns['xafs_roth'], user_ns['xafs_rots'], user_ns['xafs_ref'],
               
               user_ns['dm3_bct'], user_ns['dm3_foils'], user_ns['dm2_fs'],
               user_ns['slits3'].top, user_ns['slits3'].bottom, user_ns['slits3'].outboard, user_ns['slits3'].inboard,
               user_ns['slits3'].vsize, user_ns['slits3'].vcenter, user_ns['slits3'].hsize, user_ns['slits3'].hcenter,
               
               user_ns['slits2'].top, user_ns['slits2'].bottom, user_ns['slits2'].outboard, user_ns['slits2'].inboard,
               user_ns['slits2'].vsize, user_ns['slits2'].vcenter, user_ns['slits2'].hsize, user_ns['slits2'].hcenter,
               
               user_ns['m1'].yu, user_ns['m1'].ydo, user_ns['m1'].ydi, user_ns['m1'].xu, user_ns['m1'].xd,
               user_ns['m1'].vertical, user_ns['m1'].lateral, user_ns['m1'].pitch, user_ns['m1'].roll, user_ns['m1'].yaw,
               
               user_ns['m2'].yu, user_ns['m2'].ydo, user_ns['m2'].ydi, user_ns['m2'].xu, user_ns['m2'].xd,
               user_ns['m2'].vertical, user_ns['m2'].lateral, user_ns['m2'].pitch, user_ns['m2'].roll, user_ns['m2'].yaw, user_ns['m2_bender'],
               
               user_ns['m3'].yu, user_ns['m3'].ydo, user_ns['m3'].ydi, user_ns['m3'].xu, user_ns['m3'].xd,
               user_ns['m3'].vertical, user_ns['m3'].lateral, user_ns['m3'].pitch, user_ns['m3'].roll, user_ns['m3'].yaw,
               
               user_ns['xafs_table'].yu, user_ns['xafs_table'].ydo, user_ns['xafs_table'].ydi, user_ns['xafs_xu'], user_ns['xafs_xd'],
               user_ns['xafs_table'].vertical, user_ns['xafs_table'].pitch, user_ns['xafs_table'].roll, 
           )
    md = dict()
    table = None
    try:
        table = db[uid].table('baseline')
    except:
        pass
    for m in biglist:
        if table is None:
            try:
                md[m.name] = m.readback.get()
            except:
                pass
            try:
                md[m.name] = m.user_readback.get()
            except:
                pass
        else:
            md[m.name] = table[m.name][1]
            
    return(md)

def motor_status():
    md = motor_metadata()

    line = ' ' + '=' * 78 + '\n'
    text = '\n Energy = %.1f eV   reflection = Si(%s)   mode = %s\n' % (user_ns['dcm'].energy.readback.get(), user_ns['dcm']._crystal, user_ns['dcm'].mode)
    text += '      Bragg = %8.5f   2nd Xtal Perp  = %7.4f   Para = %8.4f\n' % \
            (user_ns['dcm'].bragg.user_readback.get(), user_ns['dcm'].perp.user_readback.get(), user_ns['dcm'].para.user_readback.get())
    text += '                                  Pitch = %7.4f   Roll = %8.4f\n\n' % \
            (user_ns['dcm_pitch'].user_readback.get(), user_ns['dcm_roll'].user_readback.get())

    text += ' M2\n      vertical = %7.3f mm            YU  = %7.3f mm\n' % (md[user_ns['m2'].vertical.name], md[user_ns['m2'].yu.name])
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'      % (md[user_ns['m2'].lateral.name],  md[user_ns['m2'].ydo.name])
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'      % (md[user_ns['m2'].pitch.name],    md[user_ns['m2'].ydi.name])
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'      % (md[user_ns['m2'].roll.name],     md[user_ns['m2'].xu.name])
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n'      % (md[user_ns['m2'].yaw.name],      md[user_ns['m2'].xd.name])
    text += '      bender   = %9.1f steps\n\n'                           %  md[user_ns['m2_bender'].name]

    stripe = '(Rh/Pt stripe)'
    if user_ns['m3'].xu.user_readback.get() < 0:
        stripe = '(Si stripe)'

    text += ' M3  %s\n'                                                 % stripe
    text += '      vertical = %7.3f mm            YU  = %7.3f mm\n'     % (md[user_ns['m3'].vertical.name], md[user_ns['m3'].yu.name])
    text += '      lateral  = %7.3f mm            YDO = %7.3f mm\n'     % (md[user_ns['m3'].lateral.name],  md[user_ns['m3'].ydo.name])
    text += '      pitch    = %7.3f mrad          YDI = %7.3f mm\n'     % (md[user_ns['m3'].pitch.name],    md[user_ns['m3'].ydi.name])
    text += '      roll     = %7.3f mrad          XU  = %7.3f mm\n'     % (md[user_ns['m3'].roll.name],     md[user_ns['m3'].xu.name])
    text += '      yaw      = %7.3f mrad          XD  = %7.3f mm\n\n'   % (md[user_ns['m3'].yaw.name],      md[user_ns['m3'].xd.name])

    text += ' Slits2:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (md[user_ns['slits2'].vsize.name], md[user_ns['slits2'].vcenter.name],
             md[user_ns['slits2'].hsize.name], md[user_ns['slits2'].hcenter.name],
             md[user_ns['slits2'].top.name], md[user_ns['slits2'].bottom.name],
             md[user_ns['slits2'].outboard.name], md[user_ns['slits2'].inboard.name])

    text += ' Slits3:  vsize  vcenter  hsize   hcenter     top    bottom    outboard  inboard\n'
    text += '        %7.3f %7.3f %7.3f %7.3f    %7.3f  %7.3f  %7.3f  %7.3f\n\n' % \
            (md[user_ns['slits3'].vsize.name], md[user_ns['slits3'].vcenter.name],
             md[user_ns['slits3'].hsize.name], md[user_ns['slits3'].hcenter.name],
             md[user_ns['slits3'].top.name], md[user_ns['slits3'].bottom.name],
             md[user_ns['slits3'].outboard.name], md[user_ns['slits3'].inboard.name])

    text += ' DM3_BCT: %7.3f mm      '   % md[user_ns['dm3_bct'].name]
    text += ' DM3_foils: %7.3f mm      ' % md[user_ns['dm3_foils'].name]
    text += ' DM2_fs: %7.3f mm\n\n'      % md[user_ns['dm2_fs'].name]

    text += ' XAFS table:\n      vertical  pitch    roll   YU     YDO     YDI\n'
    text += '       %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n\n' % \
            (md[user_ns['xafs_table'].vertical.name], md[user_ns['xafs_table'].pitch.name], md[user_ns['xafs_table'].roll.name],
             md[user_ns['xafs_table'].yu.name], md[user_ns['xafs_table'].ydo.name], md[user_ns['xafs_table'].ydi.name])

    text += ' XAFS stages (motor names are xafs_<name>, units mm or deg):\n'
    text += '     name =     x        y     pitch    wheel (slot)   ref\n'
    text += '           %8.3f %8.3f %7.3f %8.3f   %d   %8.3f\n' % \
            (md[user_ns['xafs_linx'].name],
             md[user_ns['xafs_liny'].name],
             md[user_ns['xafs_pitch'].name],
             md[user_ns['xafs_rotb'].name], user_ns['xafs_rotb'].current_slot(user_ns['xafs_rotb'].position),
             md[user_ns['xafs_ref'].name]
            )

    return text
    # return line + text + line

def ms():
    boxedtext('BMM motor status', motor_status(), 'cyan', width=84)


def motor_sidebar(md=None):
    '''Generate a list of motor positions to be used in the static html page for a scan sequence.
    Return value is a long string with html tags and entities embedded in the string.

    Parameters
    ----------
    md : dict
        dict with motor positions keyed by <motor>.name

    If md is not provided, the current motor positions will be used.
    If taking a record from Data Broker, the motor positions have been
    recorded in the baseline.  If generating a dossier from a Data
    Broker record, do:

    >>> text = motor_sidebar(uid=uid)

    where uid is the ID of the scan.
    '''
    if type(md) == str:
        md = motor_metadata(md)
    if md is None or type(md) is not dict:
        md = motor_metadata()
    motors = ''
        
    mlist = []
    mlist.append('XAFS stages:')
    mlist.append('xafs_x, %.3f, xafs_y, %.3f'         % (md[user_ns['xafs_linx'].name],  md[user_ns['xafs_liny'].name]))
    mlist.append('xafs_pitch, %.3f, xafs_roll, %.3f'  % (md[user_ns['xafs_pitch'].name], md[user_ns['xafs_roll'].name]))
    mlist.append('xafs_ref, %.3f, xafs_wheel, %.3f'   % (md[user_ns['xafs_linxs'].name], md[user_ns['xafs_wheel'].name]))
    #mlist.append('xafs_roth, %.3f, xafs_rots, %.3f'   % (md[user_ns['xafs_roth'].name],  md[user_ns['xafs_rots'].name]))
    mlist.append('wheel slot = %2d'                   % user_ns['xafs_wheel'].current_slot())
    motors += '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>dm3_bct: %.3f' % md[user_ns['dm3_bct'].name]

    mlist = []
    mlist.append('Slits3:')
    mlist.append('slits3.vsize, %.3f, slits3.vcenter, %.3f'     % (md[user_ns['slits3'].vsize.name],    md[user_ns['slits3'].vcenter.name]))
    mlist.append('slits3.hsize, %.3f, slits3.hcenter, %.3f'     % (md[user_ns['slits3'].hsize.name],    md[user_ns['slits3'].hcenter.name]))
    mlist.append('slits3.top, %.3f, slits3.bottom, %.3f'        % (md[user_ns['slits3'].top.name],      md[user_ns['slits3'].bottom.name]))
    mlist.append('slits3.outboard, %.3f, slits3.inboard, %.3f'  % (md[user_ns['slits3'].outboard.name], md[user_ns['slits3'].inboard.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('M2')
    mlist.append('m2.vertical, %.3f, m2.yu, %.3f' % (md[user_ns['m2'].vertical.name], md[user_ns['m2'].yu.name]))
    mlist.append('m2.lateral, %.3f, m2.ydo, %.3f' % (md[user_ns['m2'].lateral.name],  md[user_ns['m2'].ydo.name]))
    mlist.append('m2.pitch, %.3f, m2.ydi, %.3f'   % (md[user_ns['m2'].pitch.name],    md[user_ns['m2'].ydi.name]))
    mlist.append('m2.roll, %.3f, m2.xu, %.3f'     % (md[user_ns['m2'].roll.name],     md[user_ns['m2'].xu.name]))
    mlist.append('m2.yaw, %.3f, m2.xd, %.3f'      % (md[user_ns['m2'].yaw.name],      md[user_ns['m2'].xd.name]))
    mlist.append('m2.bender, %9.1f'               %  md[user_ns['m2_bender'].name])
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)


    mlist = []
    stripe = '(Rh/Pt stripe)'
    if md[user_ns['m3'].xu.name] < 0:
        stripe = '(Si stripe)'
    mlist.append('M3  %s' % stripe)
    mlist.append('m3.vertical, %.3f, m3.yu, %.3f' % (md[user_ns['m3'].vertical.name], md[user_ns['m3'].yu.name]))
    mlist.append('m3.lateral, %.3f, m3.ydo, %.3f' % (md[user_ns['m3'].lateral.name],  md[user_ns['m3'].ydo.name]))
    mlist.append('m3.pitch, %.3f, m3.ydi, %.3f'   % (md[user_ns['m3'].pitch.name],    md[user_ns['m3'].ydi.name]))
    mlist.append('m3.roll, %.3f, m3.xu, %.3f'     % (md[user_ns['m3'].roll.name],     md[user_ns['m3'].xu.name]))
    mlist.append('m3.yaw, %.3f, m3.xd, %.3f'      % (md[user_ns['m3'].yaw.name],      md[user_ns['m3'].xd.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('XAFS table:')
    mlist.append('xt.vertical, %.3f, xt.yu, %.3f' % (md[user_ns['xafs_table'].vertical.name], md[user_ns['xafs_table'].yu.name]))
    mlist.append('xt.pitch, %.3f, xt.ydo, %.3f'   % (md[user_ns['xafs_table'].pitch.name],    md[user_ns['xafs_table'].ydo.name]))
    mlist.append('xt.roll, %.3f, xt.ydi, %.3f'    % (md[user_ns['xafs_table'].roll.name],     md[user_ns['xafs_table'].ydi.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    mlist = []
    mlist.append('Slits2:')
    mlist.append('slits2.vsize, %.3f, slits2.vcenter, %.3f'    % (md[user_ns['slits2'].vsize.name],    md[user_ns['slits2'].vcenter.name]))
    mlist.append('slits2.hsize, %.3f, slits2.hcenter, %.3f'    % (md[user_ns['slits2'].hsize.name],    md[user_ns['slits2'].hcenter.name]))
    mlist.append('slits2.top, %.3f, slits2.bottom, %.3f'       % (md[user_ns['slits2'].top.name],      md[user_ns['slits2'].bottom.name]))
    mlist.append('slits2.outboard, %.3f, slits2.inboard, %.3f' % (md[user_ns['slits2'].outboard.name], md[user_ns['slits2'].inboard.name]))
    motors += '\n<br><br>' + '<br>\n&nbsp;&nbsp;&nbsp;'.join(mlist)

    motors += '\n<br><br>dm3_foils, %.3f' % md[user_ns['dm3_foils'].name]
    motors += '\n<br>dm2_fs, %.3f' % md[user_ns['dm2_fs'].name]

    
    return motors



def xrd_motors():
    text = '\n'
    for m in (xrd_delta,  xrd_eta,    xrd_chi,    xrd_phi,    xrd_mu,     xrd_nu,
              xrd_anal,   xrd_det,    xrd_dethor, xrd_wheel1, xrd_wheel2,
              xrd_samx,   xrd_samy,   xrd_samz,   xrd_tabyd,  xrd_tabyui,
              xrd_tabyuo, xrd_tabxu,  xrd_tabxd,  xrd_tabz,   xrd_slit1t,
              xrd_slit1b, xrd_slit1i, xrd_slit1o):
        text += '  %-26s: %8.3f %s\n' % (m.name, m.user_readback.get(), m.describe()[m.name]['units'])
    return text

def xrdm():
    boxedtext('XRD motor status', xrd_motors(), 'cyan', width=60)
