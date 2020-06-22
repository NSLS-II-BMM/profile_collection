
import json

## https://stackoverflow.com/a/22616059
import itertools, sys
spinner = itertools.cycle(['-', '\\', '|', '/'])

run_report(__file__)

def exposure(fname='spot', ncounts=1, nreps=1):
    report('SDC: counting %s for %.2f seconds, %s\n' % (inflect('time', ncounts), dwell_time.readback.get(), inflect('repetitions', nreps)), 'bold')
    for n in range(nreps):
        results = dict()
        results['filename']     = fname
        results['cradle.y']     = cradle.y.readback.get()
        results['xafs_x']       = xafs_x.user_readback.get()
        results['ring.current'] = ring.current.get()
        results['time_start']   = now()

        yield from count([dwell_time, quadem1, vor], ncounts)
        table  = db[-1].table()
        names  = {'I0'     : 'I0',
                  'ROI1'   : 'Ni',
                  'ROI2_1' : 'Zn',
                  'ROI3_1' : 'Au',
                  'ROI2'   : 'ni_zn',
                  'ROI2_2' : 'zn_au',
                  'ROI3_2' : 'au_el',
                  'DTC1'   : 'Ni (dtc)',
                  'DTC2_1' : 'Zn (dtc)',
                  'DTC3_1' : 'Au (dtc)',
                  'DTC2'   : 'ni_zn (dtc)',
                  'DTC2_2' : 'zn_au (dtc)',
                  'DTC3_2' : 'au_el (dtc)',
                  'dwti_dwell_time':'dwell_time'}

        for k in names.keys():
            results[names[k]]   = list(table[k])
        results['time_end']     = now()

        out = os.path.join(BMMuser.DATA, '%s.%3.3d' % (fname, n+1))
    
        handle = open(out, 'w')
        handle.write(json.dumps(results, indent=4) + '\n')
        ## write data table
        handle.close()
        #print('wrote %s' % out)


def image_sequence(stub='test'):
    positions = (20, 40, 60, 80, 100, 120, 140, 160, 180)
    metadata = dict()
    for p in positions:
        this = dict()
        this['I0_before']     = quadem1.I0.get()
        this['ring_current']  = ring.current.get()
        this['incident_energy'] = dcm.energy.readback.get()
        this['xafs_mtr8']     = p
        this['time_start']    = now()
        pil.number = 1
        yield from mv(xafs_mtr8, p)
        pil.fname = '%s_%3.3d' % (stub, p)
        pil.snap()
        close_all_plots()
        pil.fetch()
        this['I0_after']      = quadem1.I0.get()
        this['time_end']      = now()
        this['filename']      = pil.fullname
        this['exposure_time'] = pil.time
        this['slits3_hsize']  = slits3.hsize.readback.get()
        this['slits3_vsize']  = slits3.vsize.readback.get()
        this['xafs_x']        = xafs_x.user_readback.get()
        this['cradle_y']      = cradle.y.readback.get()
        metadata['%s-%3.3d' % (stub, p)] = this
    yield from mv(xafs_mtr8, positions[0])
    close_all_plots()

    out = os.path.join(BMMuser.DATA, '%s.json' % stub)
    handle = open(out, 'w')
    handle.write(json.dumps(metadata, indent=4) + '\n')
    handle.close()
    
        



def auscan(axis, start, stop, nsteps, pluck=True, force=False, inttime=0.1, md={}): # integration time?
    '''
    Generic linescan plan.  This is a RELATIVE scan, relative to the
    current position of the selected motor.

    For example:
       RE(linescan('cradle.y', -1, 1, 21))

       axis :    motor or nickname
       start:    starting value for a relative scan
       stop:     ending value for a relative scan
       nsteps:   number of steps in scan
       pluck:    flag for whether to offer to pluck & move motor
       force:    flag for forcing a scan even if not clear to start
       inttime:  integration time in seconds (default: 0.1)

    The motor is either the BlueSky name for a motor (e.g. xafs_linx)
    or a nickname for an XAFS sample motor (e.g. 'x' for xafs_linx).

    This does not write an ASCII data file, but it does make a log entry.

    Use the ls2dat() function to extract the linescan from the
    database and write it to a file.
    '''

    def main_plan(axis, start, stop, nsteps, pluck, force, inttime):
        (ok, text) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(text))
            yield from null()
            return

        RE.msg_hook = None
        ## sanitize input and set thismotor to an actual motor
        if type(axis) is str: axis = axis.lower()

        ## sanity checks on axis
        if axis not in motor_nicknames.keys() and 'EpicsMotor' not in str(type(axis)) \
           and 'PseudoSingle' not in str(type(axis)) and 'WheelMotor' not in str(type(axis)):
            print(error_msg('\n*** %s is not a linescan motor (%s)\n' %
                          (axis, str.join(', ', motor_nicknames.keys()))))
            yield from null()
            return

        if 'EpicsMotor' in str(type(axis)):
            thismotor = axis
        elif 'PseudoSingle' in str(type(axis)):
            thismotor = axis
        elif 'WheelMotor' in str(type(axis)):
            thismotor = axis
        else:                       # presume it's an xafs_XXXX motor
            thismotor = motor_nicknames[axis]
        BMMuser.motor = thismotor

        yield from abs_set(_locked_dwell_time, inttime, wait=True)
        dets  = [quadem1, vor]
        denominator = ''
        detname = ''
       
        funni = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC1']   / doc['data']['I0'])
        funzn = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC2_1'] / doc['data']['I0'])
        funau = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC3_1'] / doc['data']['I0'])
        
        plot = [DerivedPlot(funni, xlabel=thismotor.name, ylabel='dtc1/I0',   title='Ni signal vs. %s' % thismotor.name),
                DerivedPlot(funzn, xlabel=thismotor.name, ylabel='dtc2_1/I0', title='Zn signal vs. %s' % thismotor.name),
                DerivedPlot(funau, xlabel=thismotor.name, ylabel='dtc3_1/I0', title='Au signal vs. %s' % thismotor.name)]

        if 'PseudoSingle' in str(type(axis)):
            value = thismotor.readback.get()
        else:
            value = thismotor.user_readback.get()
        line1 = '%s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (thismotor.name, start, stop, nsteps, value)
        ##BMM_suspenders()            # engage suspenders

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf
        thismd['XDI']['Scan'] = dict()
        thismd['XDI']['Scan']['dwell_time'] = inttime

        with open(dotfile, "w") as f:
            f.write("")
                
    
        @subs_decorator(plot)
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md})

        uid = yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, uid, db[-1].start['scan_id']))
        if pluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            yield from move_after_scan(thismotor)

    
    def cleanup_plan():
        if os.path.isfile(dotfile): os.remove(dotfile)
        ##RE.clear_suspenders()       # disable suspenders
        yield from resting_state_plan()


    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a line scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    dotfile = '/home/xf06bm/Data/.line.scan.running'
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(axis, start, stop, nsteps, pluck, force, inttime), cleanup_plan())
    RE.msg_hook = BMM_msg_hook
    




def auslitscan(start=-0.2, stop=0.2, nsteps=21, pluck=False, force=False, inttime=0.3, md={}): # integration time?
    '''
    Generic linescan plan.  This is a RELATIVE scan, relative to the
    current position of the selected motor.

    For example:
       RE(auslitscan())

       start:    starting value for a relative scan
       stop:     ending value for a relative scan
       nsteps:   number of steps in scan
       pluck:    flag for whether to offer to pluck & move motor
       force:    flag for forcing a scan even if not clear to start
       inttime:  integration time in seconds (default: 0.1)

    The motor is either the BlueSky name for a motor (e.g. xafs_linx)
    or a nickname for an XAFS sample motor (e.g. 'x' for xafs_linx).

    This does not write an ASCII data file, but it does make a log entry.

    Use the ls2dat() function to extract the linescan from the
    database and write it to a file.
    '''

    def main_plan(start, stop, nsteps, pluck, force, inttime):
        (ok, text) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(text))
            yield from null()
            return

        RE.msg_hook = None

        thismotor = dm3_bct
        yield from abs_set(_locked_dwell_time, inttime, wait=True)
        yield from abs_set(thismotor.velocity, 0.4, wait=True)
        dets  = [quadem1, vor]
        denominator = ''
        detname = ''
       
        funni = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC1']   / doc['data']['I0'])
        funzn = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC2_1'] / doc['data']['I0'])
        funau = lambda doc: (doc['data'][thismotor.name], doc['data']['DTC3_1'] / doc['data']['I0'])
        
        plot = [DerivedPlot(funni, xlabel=thismotor.name, ylabel='dtc1/I0',   title='Ni signal vs. %s' % thismotor.name),
                DerivedPlot(funzn, xlabel=thismotor.name, ylabel='dtc2_1/I0', title='Zn signal vs. %s' % thismotor.name),
                DerivedPlot(funau, xlabel=thismotor.name, ylabel='dtc3_1/I0', title='Au signal vs. %s' % thismotor.name)]

        value = thismotor.user_readback.get()
        line1 = '%s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (thismotor.name, start, stop, nsteps, value)
        ##BMM_suspenders()            # engage suspenders

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf
        thismd['XDI']['Scan'] = dict()
        thismd['XDI']['Scan']['dwell_time'] = inttime

        with open(dotfile, "w") as f:
            f.write("")
                
    
        @subs_decorator(plot)
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md})

        yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
        yield from sleep(3)
        uid = yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        yield from sleep(3)
        yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, uid, db[-1].start['scan_id']))
        if pluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            yield from move_after_scan(thismotor)

    
    def cleanup_plan():
        if os.path.isfile(dotfile): os.remove(dotfile)
        ##RE.clear_suspenders()       # disable suspenders
        yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
        yield from resting_state_plan()


    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a line scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    dotfile = '/home/xf06bm/Data/.line.scan.running'
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(start, stop, nsteps, pluck, force, inttime), cleanup_plan())
    RE.msg_hook = BMM_msg_hook
    
    


def auscan2dat(datafile, key):
    '''
    Export an SDC linescan database entry to an XDI file.

      auscan2dat('/path/to/myfile.dat', 1533)

    or

      auscan2dat('/path/to/myfile.dat', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    The arguments are a data file name and the database key.
    '''
    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    handle = open(datafile, 'w')
    dataframe = db[key]
    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    abscissa = dataframe['start']['motors'][0]
    column_list = [abscissa, 'I0',
                   'DTC1', 'DTC2_1', 'DTC3_1', 'DTC2', 'DTC2_2', 'DTC3_2',
                   'ROI1', 'ROI2_1', 'ROI3_1', 'ROI2', 'ROI2_2', 'ROI3_2' ]
    template = "  %.3f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"

    table = dataframe.table()
    this = table.loc[:,column_list]

    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)
    st = pandas.Timestamp(start_time) # this is a UTC problem
    
    handle.write('# XDI/1.0 BlueSky/%s\n'          % bluesky_version)
    handle.write('# Beamline.slits3_hsize: %.3f\n' % slits3.hsize.readback.get())
    handle.write('# Beamline.slits3_vsize: %.3f\n' % slits3.vsize.readback.get())
    handle.write('# Beamline.xafs_x: %.3f\n'       % xafs_x.user_readback.get())
    handle.write('# Beamline.cradle_y: %.3f\n'     % cradle.y.readback.get())
    handle.write('# Beamline.incident_energy: %.1f\n' % dcm.energy.readback.get())
    handle.write('# Scan.start_time: %s\n'         % start_time)
    handle.write('# Scan.end_time: %s\n'           % end_time)
    handle.write('# Scan.dwell_time: %s\n'         % dataframe.start['XDI']['Scan']['dwell_time'] )
    handle.write('# Scan.transient_id: %s\n'       % dataframe.start['scan_id'])
    handle.write('# Scan.uid: %s\n'                % dataframe.start['uid'])
    handle.write('# Facility.energy: %.1f GeV\n'   % (ring.energy.get()/1000))
    handle.write('# Facility.current: %.1f\n'      % ring.current.get())
    handle.write('# Facility.mode: %s\n'           % ring.mode.get())
    handle.write('# Facility.GUP: %d\n'            % BMMuser.gup)
    handle.write('# Facility.SAF: %d\n'            % BMMuser.saf)
    handle.write('# Facility.cycle: %s\n'          % BMMuser.cycle)
    handle.write('# Column.1: %s mm\n'             % abscissa)
    handle.write('# Column.2: I0 nA\n')
    handle.write('# Column.3: dead time corrected Ni signal counts\n')
    handle.write('# Column.4: dead time corrected Zn signal counts\n')
    handle.write('# Column.5: dead time corrected Au signal counts\n')
    handle.write('# Column.6: dead time corrected signal between Ni and Zn counts\n')
    handle.write('# Column.7: dead time corrected signal between Zn and Au counts\n')
    handle.write('# Column.8: dead time corrected signal between Au and elastic counts\n')
    handle.write('# Column.9: raw Ni signal counts\n')
    handle.write('# Column.10: raw Zn signal counts\n')
    handle.write('# Column.11: raw Au signal counts\n')
    handle.write('# Column.12: raw signal between Ni and Zn counts\n')
    handle.write('# Column.13: raw signal between Zn and Au counts\n')
    handle.write('# Column.14: raw signal between Au and elastic counts\n')
    
    handle.write('# ==========================================================\n')
    handle.write('# ' + '  '.join(column_list) + '\n')
    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
    print(bold_msg('wrote linescan to %s' % datafile))
    





def sdc(slp=1):
    def main_plan():
        BMM_suspenders()
        while True:
            close_all_plots()
            stub=vor.names.name29.get()
            print('\n' + go_msg('Waiting to begin SDC exposure '), end='')
            while not bool(stub):
                sys.stdout.write(next(spinner))   # write the next character
                sys.stdout.flush()                # flush stdout buffer (actual character display)
                sys.stdout.write('\b')            # erase the last written char
                yield from sleep(slp)
                stub=vor.names.name29.get()
        
            print()
            # instructions = json.loads(trigger)
            # try:
            #     stub = instructions['key']
            # except:
            #     print(error_msg('no file stub provided in the name29 trigger'))
            #     return(yield from null())
            # try:
            #     fluotime = instructions['fluotime']
            # except:
            #     fluotime = 1
            # try:
            #     ncounts = instructions['ncounts']
            # except:
            #     ncounts = 1
            # try:
            #     nreps = instructions['nreps']
            # except:
            #     nreps = 1
            # try:
            #     piltime = instructions['piltime']
            # except:
            #     piltime = 1
            
            #yield from abs_set(_locked_dwell_time, fluotime)
            #yield from exposure(fname=stub, ncounts=ncounts, nreps=nreps)

            yield from mv(slits3.hsize, 0.15)

            # yield from mvr(cradle.y, -0.2)
            # yield from auscan(xafs_x, -3.75, 3.75, 61, inttime=1, pluck=False)
            # auscan2dat(os.path.join(BMMuser.DATA, '%s_linescan_down.dat' % stub), db[-1].start['uid'])
            # close_all_plots()

            yield from auslitscan()
            auscan2dat(os.path.join(BMMuser.DATA, '%s_slitscan.dat' % stub), db[-1].start['uid'])
            
            yield from abs_set(_locked_dwell_time, 0.5)
            close_all_plots()

            yield from mv(slits3.vsize, 0.1)
            yield from mv(slits3.hsize, 0.3)
            pil.fname = stub
            #pil.time = piltime
            yield from image_sequence(stub=stub)
            yield from mv(slits3.vsize, 0.05)
            yield from mv(slits3.hsize, 0.15)
            
            image_web = os.path.join(BMMuser.DATA, 'snapshots', '%s.jpg'%stub)
            annotation = 'NIST BMM (NSLS-II 06BM)      ' + stub + '      ' + now()
            snap('XAS', filename=image_web, annotation=annotation)

        
            vor.names.name29.put('')
    
            report('\nwrote %s\nand %s\n' % (os.path.join(BMMuser.DATA, stub+'.*'), pil.fullname))

    def cleanup_plan():
        vor.names.name29.put('')
        yield from abs_set(_locked_dwell_time, 0.5)
        close_all_plots()
        RE.msg_hook = BMM_msg_hook
        
        
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(), cleanup_plan())
    RE.msg_hook = BMM_msg_hook

    
    
