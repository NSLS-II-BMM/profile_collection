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


def write_XDI(datafile, dataframe, mode, comment):
    handle = open(datafile, 'w')

    ## set Scan.start_time & Scan.end_time ... this is how it is done
    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)

    if 'trans' in mode:
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
    if 'fluo' in mode or 'both' in mode:
        xdi.append('# Detector.fluorescence: %s'        % dataframe.start['XDI,Detector,fluorescence'])
        xdi.append('# Detector.deadtime_correction: %s' % dataframe.start['XDI,Detector,deadtime_correction'])
    if 'yield' in mode:
        xdi.append('# Detector.yield: %s'               % dataframe.start['XDI,Detector,yield'])

    xdi.extend(['# Element.symbol: %s'              % dataframe.start['XDI,Element,symbol'],
                '# Element.edge: %s'                % dataframe.start['XDI,Element,edge'],
                '# Facility.name: %s'               % 'NSLS-II',
                '# Facility.current: %s'            % dataframe.start['XDI,Facility,current'],
                '# Facility.energy: %s'             % dataframe.start['XDI,Facility,energy'],
                '# Facility.mode: %s'               % dataframe.start['XDI,Facility,mode'],
                '# Mono.name: %s'                   % dataframe.start['XDI,Mono,name'],
                '# Mono.d_spacing: %s'              % dataframe.start['XDI,Mono,d_spacing'],
                '# Mono.encoder_resolution: %.7f deg/ct' % dataframe.start['XDI,Mono,encoder_resolution'],
                '# Mono.angle_offset: %.7f deg'     % dataframe.start['XDI,Mono,angle_offset'],
                '# Mono.scan_mode: %s'              % dataframe.start['XDI,Mono,scan_mode'],
                '# Mono.scan_type: %s'              % dataframe.start['XDI,Mono,scan_type'],
                '# Mono.direction: %s in energy'    % dataframe.start['XDI,Mono,direction'],
                '# Mono.first_crystal_temperature: %.1f C'  % dataframe.start['XDI,Mono,first_crystal_temperature'],
                '# Mono.compton_shield_temperature: %.1f C' % dataframe.start['XDI,Mono,compton_shield_temperature'],
                '# Sample.name: %s'                 % dataframe.start['XDI,Sample,name'],
                '# Sample.prep: %s'                 % dataframe.start['XDI,Sample,prep'],
                '# Sample.x_position: %.3f'         % dataframe.start['XDI,Sample,x_position'],
                '# Sample.y_position: %.3f'         % dataframe.start['XDI,Sample,y_position'], # what about linxs, pitch, rotX ???
                '# Sample.roll_position: %.3f'      % dataframe.start['XDI,Sample,roll_position'],
                '# Scan.experimenters: %s'          % dataframe.start['XDI,Scan,experimenters'],
                '# Scan.edge_energy: %.1f'          % float(dataframe.start['XDI,Scan,edge_energy']),
                '# Scan.start_time: %s'             % start_time,
                '# Scan.end_time: %s'               % end_time,
                '# Scan.transient_id: %s'           % dataframe.start['scan_id'],
                '# Scan.uid: %s'                    % dataframe.start['uid'],
            ])
    plot_hint = 'ln(I0/It)  --  ln($4/$5)'
    if 'fluo' in mode or 'both' in mode:
        plot_hint = '(DTC1 + DTC2 + DTC3 + DTC4) / I0  --  ($7+$8+$9+$10) / $4'
    elif 'yield' in mode:
        plot_hint = 'ln(Iy/I0  --  ln($7/$4)'
    elif 'ref' in mode:
        plot_hint = 'ln(It/Ir  --  ln($5/$6)'
    xdi.append('# Scan.plot_hint: %s' % plot_hint)
    labels = []
    for i, col in enumerate(('energy', 'requested_energy', 'measurement_time'), start=1):     # 'encoder'
        xdi.append('# Column.%d: %s %s' % (i, col, units(col)))
        labels.append(col)

    ## keeping this up-to-date is key!
    # name_map = {'3': 'roi1',  '7': 'icr1', '11': 'ocr1',
    #             '4': 'roi2',  '8': 'icr2', '12': 'ocr2',
    #             '5': 'roi3',  '9': 'icr3', '13': 'ocr3',
    #             '6': 'roi4', '10': 'icr4', '14': 'ocr4'}

    ## generate a list of column lables & Column.N metadatum lines
    for i, d in enumerate(detectors, start=4):
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
    if 'fluo' in mode or 'both' in mode:
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'I0', 'It', 'Ir']
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f\n"
        if 'yield' in mode:
            column_list.append('Iy')
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f\n"

    this = table.loc[:,column_list]

    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
