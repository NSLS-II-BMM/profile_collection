from bluesky import __version__ as bluesky_version
import re

def units(label):
    label = label.lower()
    if 'energy' in label:
        return 'eV'
    elif 'time' in label:
        return 'seconds'
    elif label in ('i0', 'it', 'ir'):
        return 'nA'
    elif label[:-1] in ('roi', 'icr', 'ocr'):
        return 'counts'
    elif 'corr' in label:
        return 'dead-time corrected count rate'
    elif 'encoder' in label:
        return 'counts'
    else:
        return ''



def write_XDI(datafile, dataframe, mode, comment):
    #handle = open(datafile, 'w')

    ## set Scan.start_time & Scan.end_time ... this is how it is done
    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)

    if 'fluo' in mode:
        detectors = fluorescence
    else:
        detectors = transmission

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
    if 'fluo' in mode:
        xdi.append('# Detector.fluorescence: %s' % dataframe.start['XDI,Detector,fluorescence'])
    xdi.extend(['# Element.symbol: %s'              % dataframe.start['XDI,Element,symbol'],
                '# Element.edge: %s'                % dataframe.start['XDI,Element,edge'],
                '# Facility.name: %s'               % 'NSLS-II',
                '# Facility.current: %.1f mA'       % ring.current.value,
                '# Facility.energy: %.1f GeV'       % (ring.energy.value/1000.),
                '# Mono.name: Si(%s)'               % dcm.crystal,
                '# Mono.d_spacing: %.7f Å'          % (dcm._twod/2),
                '# Mono.scan_mode: %s'              % dataframe.start['XDI,Mono,scan_mode'],
                '# Mono.scan_type: %s'              % dataframe.start['XDI,Mono,scan_type'],
                '# Mono.direction: %s in energy'    % 'forward',                               # <------- bothways!
                '# Sample.name: %s'                 % dataframe.start['XDI,Sample,name'],
                '# Sample.prep: %s'                 % dataframe.start['XDI,Sample,prep'],
                '# Scan.edge_energy: %.1f'          % float(dataframe.start['XDI,Scan,edge_energy']),
                '# Scan.start_time: %s'             % start_time,
                '# Scan.end_time: %s'               % end_time,
                '# Scan.transient_id: %s'           % dataframe.start['scan_id'],
                '# Scan.uid: %s'                    % dataframe.stop['uid'],
            ])
    plot_hint = 'ln(I0/It)  --  ln($5/$6)'
    if 'fluo' in mode:
        plot_hint = '(dtcorr1 + dtcorr2 + dtcorr3 + dtcorr4) / I0  --  ($8+$9+$10+$11) / $5'
    xdi.append('# Scan.plot_hint: %s' % plot_hint)
    labels = []
    for i, col in enumerate(('energy', 'requested_energy', 'encoder', 'measurement_time'), start=1):
        xdi.append('# Column.%d: %s %s' % (i, col, units(col)))
        labels.append(col)

    ## keeping this up-to-date is key!
    name_map = {'3': 'roi1',  '7': 'icr1', '11': 'ocr1',
                '4': 'roi2',  '8': 'icr2', '12': 'ocr2',
                '5': 'roi3',  '9': 'icr3', '13': 'ocr3',
                '6': 'roi4', '10': 'icr4', '14': 'ocr4'}

    ## generate a list of column lables & Column.N metadatum lines
    for i, d in enumerate(detectors, start=5):
        if 'quadem1' in d.name:
            this = re.sub('quadem1_', '', d.name)
        elif 'vortex_me4_channels_chan' in d.name:
            this = re.sub('vortex_me4_channels_chan', '', d.name)
            this = name_map[this]
        elif 'vortex_me4_' in d.name:
            this = re.sub('vortex_me4_', '', d.name)
        else:
            this = d.name
        labels.append(this)
        xdi.append('# Column.%d: %s %s' % (i, this, units(this)))

    ## write it all out
    for line in xdi:
        print(line)             # handle.write(line)
    print('# ///////////')
    print('# ' + comment)
    print('# -----------')
    print('# ' + '  '.join(labels))
    # handle.flush()

    ## grab columns
    # table = dataframe.table()
    ## munge rows/columns
    # handle.write(row)

    # handle.flush()
    # handle.close
