from bluesky import __version__ as bluesky_version
import re

run_report(__file__)

def units(label):
    label = label.lower()
    if 'energy' in label:
        return 'eV'
    elif 'time' in label:
        return 'seconds'
    elif label in ('i0', 'it', 'ir', 'iy'):
        return 'nA'
    elif label[:-1] in ('roi', 'icr', 'ocr'):
        return 'counts'
    elif 'corr' in label:
        return 'dead-time corrected count rate'
    elif 'dtc' in label:
        return 'dead-time corrected count rate'
    elif 'encoder' in label:
        return 'counts'
    else:
        return ''


_ionchambers = [quadem1.I0, quadem1.It, quadem1.Ir]
_vortex_ch1  = [vor.channels.chan3, vor.channels.chan7,  vor.channels.chan11]
_vortex_ch2  = [vor.channels.chan4, vor.channels.chan8,  vor.channels.chan12]
_vortex_ch3  = [vor.channels.chan5, vor.channels.chan9,  vor.channels.chan13]
_vortex_ch4  = [vor.channels.chan6, vor.channels.chan10, vor.channels.chan14]
_vortex      = _vortex_ch1 + _vortex_ch2 + _vortex_ch3 + _vortex_ch4
_deadtime_corrected = [vor.dtcorr1, vor.dtcorr2, vor.dtcorr3, vor.dtcorr4]

transmission = _ionchambers
fluorescence = _ionchambers + _deadtime_corrected + _vortex


def write_XDI(datafile, dataframe, mode, comment, kind='xafs'):
    handle = open(datafile, 'w')

    ## set Scan.start_time & Scan.end_time ... this is how it is done
    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)
    st = pandas.Timestamp(start_time) # this is a UTC problem

    if 'trans' in mode:
        detectors = transmission
    elif 'test' in mode:
        detectors = transmission
    elif 'ref' in mode:
        detectors = transmission
    else:
        detectors = fluorescence

    ## snarf XDI metadata from the dataframe and elsewhere
    xdi = list(['# XDI/1.0 BlueSky/%s'              % bluesky_version,
                '# Beamline.name: %s'               % dataframe.start['XDI,Beamline,name'],
                '# Beamline.xray_source: %s'        % dataframe.start['XDI,Beamline,xray_source'],
                '# Beamline.collimation: %s'        % dataframe.start['XDI,Beamline,collimation'],
                '# Beamline.focusing: %s'           % dataframe.start['XDI,Beamline,focusing'],
                '# Beamline.harmonic_rejection: %s' % dataframe.start['XDI,Beamline,harmonic_rejection'],
                '# Detector.I0: %s'                 % dataframe.start['XDI,Detector,I0'],
                '# Detector.I1: %s'                 % dataframe.start['XDI,Detector,It'],
                '# Detector.I2: %s'                 % dataframe.start['XDI,Detector,Ir'],])
    if 'fluo' in mode or 'flou' in mode or 'both' in mode:
        xdi.append('# Detector.fluorescence: %s'        % dataframe.start['XDI,Detector,fluorescence'])
        xdi.append('# Detector.deadtime_correction: %s' % dataframe.start['XDI,Detector,deadtime_correction'])
    if 'yield' in mode:
        xdi.append('# Detector.yield: %s'               % dataframe.start['XDI,Detector,yield'])

    if kind == 'xafs':
        xdi.extend(['# Element.symbol: %s'              % dataframe.start['XDI,Element,symbol'],
                    '# Element.edge: %s'                % dataframe.start['XDI,Element,edge'],])

    try:
        ring_current = dataframe.table('baseline')['ring_current'][1]
    except:
        ring_current = 0
    xdi.extend(['# Facility.name: %s'               % 'NSLS-II',
                '# Facility.current: %.1f mA'       % ring_current,
                '# Facility.energy: %s'             % dataframe.start['XDI,Facility,energy'],
                '# Facility.mode: %s'               % dataframe.start['XDI,Facility,mode'],
                '# Facility.GUP: %d'                % dataframe.start['XDI,Facility,GUP'],
                '# Facility.SAF: %d'                % dataframe.start['XDI,Facility,SAF'],
                '# Mono.name: %s'                   % dataframe.start['XDI,Mono,name'],
                '# Mono.d_spacing: %s'              % dataframe.start['XDI,Mono,d_spacing'],
                '# Mono.encoder_resolution: %.7f deg/ct' % dataframe.start['XDI,Mono,encoder_resolution'],
                '# Mono.angle_offset: %.7f deg'     % dataframe.start['XDI,Mono,angle_offset'],
                '# Mono.scan_mode: %s'              % dataframe.start['XDI,Mono,scan_mode'],
                '# Mono.scan_type: %s'              % dataframe.start['XDI,Mono,scan_type'],
                '# Mono.direction: %s in energy'    % dataframe.start['XDI,Mono,direction'],])
    
    if XDI_record['xafs_linx'] :
        xdi.append('# Sample.x_position: %.3f mm'         % dataframe.table('baseline')['xafs_linx'][1])
    if XDI_record['xafs_liny'] :
        xdi.append('# Sample.y_position: %.3f mm'         % dataframe.table('baseline')['xafs_liny'][1])
    if XDI_record['xafs_roll'] :
        xdi.append('# Sample.roll_position: %.3f deg'     % dataframe.table('baseline')['xafs_roll'][1])
    if XDI_record['xafs_pitch'] :
        xdi.append('# Sample.pitch_position: %.3f deg'    % dataframe.table('baseline')['xafs_pitch'][1])
    if XDI_record['xafs_linxs'] :
        xdi.append('# Sample.xs_position: %.3f mm'        % dataframe.table('baseline')['xafs_linxs'][1])
    if XDI_record['xafs_lins'] :
        xdi.append('# Sample.s_position: %.3f mm'         % dataframe.table('baseline')['xafs_lins'][1])
    if XDI_record['xafs_rotb'] :
        xdi.append('# Sample.rotb_position: %.3f mm'      % dataframe.table('baseline')['xafs_rotb'][1])
    if XDI_record['xafs_rots'] :
        xdi.append('# Sample.rots_position: %.3f mm'      % dataframe.table('baseline')['xafs_rots'][1])
    if XDI_record['xafs_roth'] :
        xdi.append('# Sample.roth_position: %.3f mm'      % dataframe.table('baseline')['xafs_roth'][1])
    if XDI_record['first_crystal_temperature'] :
        xdi.append('# Mono.first_crystal_temperature: %.1f C'  % dataframe.table('baseline')['first_crystal_temperature'][1])
    if XDI_record['compton_shield_temperature'] :
        xdi.append('# Mono.compton_shield_temperature: %.1f C' % dataframe.table('baseline')['compton_shield_temperature'][1])
    if XDI_record['bpm_upstream_x'] :
        xdi.append('# Facility.bpm_upstream_x: %.3f mm'   % dataframe.table('baseline')['bpm_upstream_x'][1])
    if XDI_record['bpm_upstream_y'] :
        xdi.append('# Facility.bpm_upstream_y: %.3f mm'   % dataframe.table('baseline')['bpm_upstream_y'][1])
    if XDI_record['bpm_downstream_x'] :
        xdi.append('# Facility.bpm_downstream_x: %.3f mm' % dataframe.table('baseline')['bpm_downstream_x'][1])
    if XDI_record['bpm_downstream_y'] :
        xdi.append('# Facility.bpm_downstream_y: %.3f mm' % dataframe.table('baseline')['bpm_downstream_y'][1])
    if XDI_record['monotc_inboard_temperature'] :
        xdi.append('# Mono.tc_inboard: %.2f C' % dataframe.table('baseline')['monotc_inboard_temperature'][1])
    if XDI_record['monotc_downstream_temperature'] :
        xdi.append('# Mono.tc_downstream: %.2f C' % dataframe.table('baseline')['monotc_downstream_temperature'][1])
    if XDI_record['monotc_upstream_high_temperature'] :
        xdi.append('# Mono.tc_upstream_high: %.2f C' % dataframe.table('baseline')['monotc_upstream_high_temperature'][1])
    if XDI_record['monotc_upstream_low_temperature'] :
        xdi.append('# Mono.tc_upstream_low: %.2f C' % dataframe.table('baseline')['monotc_upstream_low_temperature'][1])

    #    t=db[-1].table('baseline')
    #    for e in sd.baseline:
    #        print('%-30s : %.3f  %.3f' % (e.name, t[e.name][1], t[e.name][2]))
    


                
    xdi.extend(['# Sample.name: %s'                 % dataframe.start['XDI,Sample,name'],
                '# Sample.prep: %s'                 % dataframe.start['XDI,Sample,prep'],
                '# Scan.experimenters: %s'          % dataframe.start['XDI,Scan,experimenters'],
                '# Scan.edge_energy: %.1f'          % float(dataframe.start['XDI,Scan,edge_energy']),
                '# Scan.start_time: %s'             % start_time,
                '# Scan.end_time: %s'               % end_time,
                '# Scan.transient_id: %s'           % dataframe.start['scan_id'],
                '# Scan.uid: %s'                    % dataframe.start['uid'],
            ])
    if kind == 'sead':
        xdi.extend(['# Beamline.energy: %.3f'   % dataframe['start']['XDI,Beamline,energy'],
                    '# Scan.dwell_time: %d'     % dataframe['start']['XDI,Scan,dwell_time'],
                    '# Scan.delay: %d'          % dataframe['start']['XDI,Scan,delay'],])
        
    plot_hint = 'ln(I0/It)  --  ln($5/$6)'
    if kind == 'sead': plot_hint = 'ln(I0/It)  --  ln($3/$4)'
    if 'fluo' in mode or 'flou' in mode or 'both' in mode:
        plot_hint = '(DTC1 + DTC2 + DTC3 + DTC4) / I0  --  ($8+$9+$10+$11) / $5'
        if kind == 'sead': plot_hint = '(DTC1 + DTC2 + DTC3 + DTC4) / I0  --  ($6+$7+$8+$9) / $3'
    elif 'yield' in mode:
        plot_hint = 'ln(Iy/I0  --  ln($8/$5)'
    elif 'test' in mode:
        plot_hint = 'I0  --  $5'
    elif 'ref' in mode:
        plot_hint = 'ln(It/Ir  --  ln($6/$7)'
    xdi.append('# Scan.plot_hint: %s' % plot_hint)
    labels = []
    abscissa_columns = ('energy', 'requested_energy', 'measurement_time', 'xmu')
    if kind == 'sead': abscissa_columns = ('time',)
    for i, col in enumerate(abscissa_columns, start=1):     # 'encoder'
        xdi.append('# Column.%d: %s %s' % (i, col, units(col)))
        labels.append(col)

    ## keeping this up-to-date is key!
    # name_map = {'3': 'roi1',  '7': 'icr1', '11': 'ocr1',
    #             '4': 'roi2',  '8': 'icr2', '12': 'ocr2',
    #             '5': 'roi3',  '9': 'icr3', '13': 'ocr3',
    #             '6': 'roi4', '10': 'icr4', '14': 'ocr4'}

    ## generate a list of column lables & Column.N metadatum lines
    for i, d in enumerate(detectors, start=len(abscissa_columns)+1):
        if 'quadem1' in d.name:
            this = re.sub('quadem1_', '', d.name)
        # elif 'vor_channels_chan' in d.name:
        #     this = re.sub('vor_channels_chan', '', d.name)
        #     this = name_map[this]
        elif 'vor_' in d.name:
            this = re.sub('vor_', '', d.name)
        else:
            this = d.name
        labels.append(this)
        xdi.append('# Column.%d: %s %s' % (i, this, units(this)))

    ## write it all out
    eol = '\n'
    for line in xdi:
        handle.write(line + eol)
    handle.write('# ///////////' + eol)
    handle.write('# ' + comment + eol)
    handle.write('# -----------' + eol)
    handle.write('# ' + '  '.join(labels) + eol)
    table = dataframe.table()
    if 'fluo' in mode or 'flou' in mode or 'both' in mode:
        table['xmu'] = (table['DTC1'] + table['DTC2'] + table['DTC3'] + table['DTC4']) / table['I0']
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        if 'yield' in mode:     # yield is the primary measurement
            table['xmu'] = table['Iy'] / table['I0']
        elif 'ref' in mode:     # reference is the primary measurement
            table['xmu'] = numpy.log(table['It'] / table['Ir'])
        elif 'test' in mode:    # test scan, no log!
            table['xmu'] = table['I0']
        else:                   # transmission is the primary measurement
            table['xmu'] = numpy.log(table['I0'] / table['It'])
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir']
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f\n"
        if 'yield' in mode:
            column_list.append('Iy')
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
    if kind == 'sead':
        column_list.pop(0)
        column_list.pop(0)
        column_list.pop(0)
        column_list.insert(0, 'time')
        template = template[12:]
    this = table.loc[:,column_list]

    for i in range(0,len(this)):
        datapoint = list(this.iloc[i])
        if kind == 'sead':
            ti = this.iloc[i, 0]
            elapsed =  (ti.value - st.value)/10**9
            datapoint[0] = elapsed
        handle.write(template % tuple(datapoint))
        #handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
