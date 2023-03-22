from bluesky import __version__ as bluesky_version
import re, pathlib, sys, datetime, pandas, numpy

from BMM.functions import plotting_mode

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


def units(label):
    label = label.lower()
    try:
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
        elif 'xs' in label:
            return 'dead-time corrected count rate'
        elif 'encoder' in label:
            return 'counts'
        elif user_ns['BMMuser'].xschannel1 in label:
            return 'dead-time corrected count rate'
        else:
            return ''
    except:
        return ''


quadem1, vor = user_ns['quadem1'], user_ns['vor']
_ionchambers = [quadem1.I0, quadem1.It, quadem1.Ir]
_vortex_ch1  = [vor.channels.chan3, vor.channels.chan7,  vor.channels.chan11]
_vortex_ch2  = [vor.channels.chan4, vor.channels.chan8,  vor.channels.chan12]
_vortex_ch3  = [vor.channels.chan5, vor.channels.chan9,  vor.channels.chan13]
_vortex_ch4  = [vor.channels.chan6, vor.channels.chan10, vor.channels.chan14]
_vortex      = _vortex_ch1 + _vortex_ch2 + _vortex_ch3 + _vortex_ch4
_deadtime_corrected = [vor.dtcorr1, vor.dtcorr2, vor.dtcorr3, vor.dtcorr4]

transmission = _ionchambers
eyield       = [quadem1.I0, quadem1.It, quadem1.Ir, quadem1.Iy]
fluorescence = _ionchambers + _deadtime_corrected + _vortex
fluorescence_1ch = [quadem1.I0, quadem1.It, quadem1.Ir, vor.dtcorr1, vor.channels.chan3, vor.channels.chan7,  vor.channels.chan11]
#xspress      = _ionchambers + [user_ns['quadem1'].xschannel1]
#xspress      = _ionchambers + [xs.channel1.rois.roi02.value]

class metadata_for_XDI_file():
    def __init__(self):
        self.xdilist = []
        self.dataframe = None

    def insert_line(self, line):
        '''Insert a line directly into the list of header lines. Presumably,
        this is already formatted suitably for XDI.'''
        self.xdilist.append(line)
        
    def start_doc(self, template, datum):
        '''Insert a header line using metadata from the start document.

        template is a string with formatting elements, for instance

            '# Beamline.name: %s'

        the first part of the template string contains the
        XDI-formatted metadatum name. After the colon is a formatting code 
        used to capture the datum from the start document.

        datum is a string which will be broken apart to find the
        metadataum.  To continue the example above, this string would be:

            'XDI.Beamline.name'

        indicating that db[key].start['XDI']['Beamline']['name'] is
        the correct value from the start document to use.  The string
        is split along the dots and the substrings are used as dictionary
        keys in the start document.

        The formatted string is then inserted into the list of header lines.
        '''
        text = ''
        (group,family,key) = datum.split('.') # e.g. XDI.Beamline.name
        try:
            text = template % self.dataframe.start[group][family][key]
        except:
            if '%s' in template:
                text = template % ''
            else:            
                text = template % 0
        self.xdilist.append(text)



def write_XDI(datafile, dataframe):
    BMMuser, xafs_wheel, ga = user_ns['BMMuser'], user_ns['xafs_wheel'], user_ns['ga']
    handle = open(datafile, 'w')

    ## set Scan.start_time & Scan.end_time ... this is how it is done
    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)
    st = pandas.Timestamp(start_time) # this is a UTC problem

    ##################################
    # grab the "underscore" metadata #
    ##################################
    try:
        mode = dataframe.start['XDI']['_mode'][0]
    except:
        mode = 'transmission'

    try:
        comment = dataframe.start['XDI']['_comment'][0]
    except:
        comment = ''

    try:
        kind = dataframe.start['XDI']['_kind']
    except:
        kind = 'xafs'

    ##########################
    # grab the detector list #
    ##########################
    mm = plotting_mode(mode)
    if 'trans' in mm:
        detectors = transmission
    elif 'test' in mm:
        detectors = transmission
    elif 'ref' in mm:
        detectors = transmission
    elif 'yield' in mm:
        detectors = eyield
    elif 'xs1' in mm:
        detectors = _ionchambers + [BMMuser.xschannel8,]
    elif 'xs' in mm:
        detectors = _ionchambers + [BMMuser.xschannel1, BMMuser.xschannel2, BMMuser.xschannel3, BMMuser.xschannel4]
    else:
        detectors = fluorescence
        if BMMuser.detector == 1:
            detectors = fluorescence_1ch
            
        

    ############################################
    # start gathering formatted metadata lines #
    ############################################
    metadata = metadata_for_XDI_file()
    metadata.dataframe = dataframe

    ## snarf XDI metadata from the dataframe and elsewhere
    metadata.insert_line('# XDI/1.0 BlueSky/%s BMM/%s' % (bluesky_version, pathlib.Path(sys.executable).parts[-3]))
    metadata.start_doc('# Beamline.name: %s',               'XDI.Beamline.name')
    metadata.start_doc('# Beamline.xray_source: %s',        'XDI.Beamline.xray_source')
    metadata.start_doc('# Beamline.collimation: %s',        'XDI.Beamline.collimation')
    metadata.start_doc('# Beamline.focusing: %s',           'XDI.Beamline.focusing')
    metadata.start_doc('# Beamline.harmonic_rejection: %s', 'XDI.Beamline.harmonic_rejection')
    metadata.start_doc('# Beamline.software: %s',           'XDI.Beamline.software')
    metadata.start_doc('# Detector.I0: %s',                 'XDI.Detector.I0')
    metadata.start_doc('# Detector.I1: %s',                 'XDI.Detector.It')
    metadata.start_doc('# Detector.I2: %s',                 'XDI.Detector.Ir')
    if 'fluo' in mode or 'flou' in mode or 'both' in mode:
        metadata.start_doc('# Detector.fluorescence: %s',        'XDI.Detector.fluorescence')
        metadata.start_doc('# Detector.deadtime_correction: %s', 'XDI.Detector.deadtime_correction')
    if 'xs' in mode:
        metadata.start_doc('# Detector.fluorescence: %s',        'XDI.Detector.fluorescence')
        metadata.start_doc('# Detector.deadtime_correction: %s', 'XDI.Detector.deadtime_correction')
    if 'yield' in mode:
        metadata.start_doc('# Detector.electron_yield: %s', 'XDI.Detector.yield')
    metadata.start_doc('# Element.symbol: %s', 'XDI.Element.symbol')
    metadata.start_doc('# Element.edge: %s',   'XDI.Element.edge')
    if kind != 'sead':
        metadata.start_doc('# Element.reference: %s',          'XDI.Element.reference')
        metadata.start_doc('# Element.reference_material: %s', 'XDI.Element.reference_material')

    #try:
    #    ring_current = dataframe.table('baseline')['ring_current'][1]
    #except:
    #    ring_current = 0
    metadata.insert_line('# Facility.name: %s' % 'NSLS-II')
    metadata.start_doc('# Facility.energy: %s',                  'XDI.Facility.energy')
    metadata.start_doc('# Facility.current: %s',                 'XDI.Facility.current')
    metadata.start_doc('# Facility.mode: %s',                    'XDI.Facility.mode')
    metadata.start_doc('# Facility.GUP: %s',                     'XDI.Facility.GUP')
    metadata.start_doc('# Facility.SAF: %s',                     'XDI.Facility.SAF')
    metadata.start_doc('# Facility.cycle: %s',                   'XDI.Facility.cycle')
    metadata.start_doc('# Mono.name: %s',                        'XDI.Mono.name')
    metadata.start_doc('# Mono.d_spacing: %s',                   'XDI.Mono.d_spacing')
    metadata.start_doc('# Mono.encoder_resolution: %.7f deg/ct', 'XDI.Mono.encoder_resolution')
    metadata.start_doc('# Mono.angle_offset: %.7f deg',          'XDI.Mono.angle_offset')
    metadata.start_doc('# Mono.scan_mode: %s',                   'XDI.Mono.scan_mode')
    metadata.start_doc('# Mono.scan_type: %s',                   'XDI.Mono.scan_type')
    metadata.start_doc('# Mono.direction: %s in energy',         'XDI.Mono.direction')
    metadata.start_doc('# Sample.name: %s',                      'XDI.Sample.name')
    metadata.start_doc('# Sample.prep: %s',                      'XDI.Sample.prep')

    if BMMuser.instrument == 'sample wheel':
        metadata.insert_line(f'# Sample.stage: {BMMuser.instrument}, slot {xafs_wheel.current_slot()}, {xafs_wheel.slot_ring()} ring')
    elif BMMuser.instrument == 'glancing angle stage':
        metadata.insert_line(f'# Sample.stage: {BMMuser.instrument}, spinner {ga.current()}')
    elif 'linkam' in BMMuser.instrument.lower():
        metadata.insert_line(f'# Sample.stage: {BMMuser.instrument}, temperature {user_ns["linkam"].readback.get():.1f}K')
    elif 'lakeshore' in BMMuser.instrument.lower():
        metadata.insert_line(f'# Sample.temperature_a: {BMMuser.instrument}, sensor A {user_ns["lakeshore"].sample_a.get():.1f}K')
        metadata.insert_line(f'# Sample.temperature_b: {BMMuser.instrument}, sensor B {user_ns["lakeshore"].sample_b.get():.1f}K')
      
    ## record selected baseline measurements as XDI metadata
    XDI_record = user_ns['XDI_record']
    for r in XDI_record.keys():
        if XDI_record[r][0] is True:
            if r in dataframe.table('baseline'):
                metadata.insert_line('# %s: %.3f mm' % (XDI_record[r][1], dataframe.table('baseline')[r][1]))
    
    metadata.start_doc('# Scan.experimenters: %s', 'XDI.Scan.experimenters')
    metadata.start_doc('# Scan.edge_energy: %s',   'XDI.Scan.edge_energy')

    if kind == '333':
        try:
            ththth_energy = dataframe.start['XDI']['Scan']['edge_energy'] / 3.0
            metadata.insert_line('# Scan.edge_energy_333: %.1f'  % ththth_energy)
        except:
            pass

    metadata.insert_line('# Scan.start_time: %s'   % start_time)
    metadata.insert_line('# Scan.end_time: %s'     % end_time)
    metadata.insert_line('# Scan.transient_id: %s' % dataframe.start['scan_id'])
    metadata.insert_line('# Scan.uid: %s'          % dataframe.start['uid'])

    if kind == 'sead':
        metadata.start_doc('# Beamline.energy: %.3f eV',      'XDI.Beamline.energy')
        metadata.start_doc('# Scan.dwell_time: %.3f seconds', 'XDI.Scan.dwell_time')
        metadata.start_doc('# Scan.delay: %.3f seconds',      'XDI.Scan.delay')


    ###############################
    # plot hint and column labels #
    ###############################
    plot_hint = 'ln(I0/It)  --  ln($5/$6)'
    if kind == 'sead': plot_hint = 'ln(I0/It)  --  ln($3/$4)'
    mm = plotting_mode(mode)
    if mm == 'xs1':
        plot_hint = f'{BMMuser.xs8}/I0  --  $8/$5'
    elif mm == 'xs' and type == 'sead':
        plot_hint = f'({BMMuser.xs1}+{BMMuser.xs2}+{BMMuser.xs3}+{BMMuser.xs4})/I0  --  ($5+$6+$7+$8)/$5'
    elif mm == 'xs':
        plot_hint = f'({BMMuser.xs1}+{BMMuser.xs2}+{BMMuser.xs3}+{BMMuser.xs4})/I0  --  ($8+$9+$10+$11)/$5'
    elif 'fluo' in mode or 'flou' in mode or 'both' in mode:
        plot_hint = '(%s + %s + %s + %s) / I0  --  ($8+$9+$10+$11) / $5' % (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4)
        if kind == 'sead': plot_hint = '(%s + %s + %s) / I0  --  ($6+$7+$9) / $3' % (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc4)
        if BMMuser.detector == 1: plot_hint = '%s / I0  --  ($8+$9+$10+$11) / $5' % BMMuser.dtc1
    elif 'yield' in mode:
        plot_hint = 'Iy/I0  --  $8/$5'
    elif 'test' in mode:
        plot_hint = 'I0  --  $2'
    elif 'ref' in mode:
        plot_hint = 'ln(It/Ir)  --  ln($6/$7)'
    metadata.insert_line('# Scan.plot_hint: %s' % plot_hint)
    labels = []
    abscissa_columns = ('energy', 'requested_energy', 'measurement_time', 'xmu')
    if kind == 'sead': abscissa_columns = ('time',)
    for i, col in enumerate(abscissa_columns, start=1):     # 'encoder'
        metadata.insert_line('# Column.%d: %s %s' % (i, col, units(col)))
        labels.append(col)

    ###############################################################
    # generate a list of column lables & Column.N metadatum lines #
    ###############################################################
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
        metadata.insert_line('# Column.%d: %s %s' % (i, this, units(this)))

    ####################
    # write it all out #
    ####################
    eol = '\n'
    for line in metadata.xdilist:
        handle.write(line + eol)
    handle.write('# ///////////' + eol)
    handle.write('# ' + comment + eol)
    handle.write('# -----------' + eol)
    handle.write('# ' + '  '.join(labels) + eol)
    table = dataframe.table()
    if plotting_mode(mode) == 'xs1':
        table['xmu'] = table[BMMuser.xs8] / table['I0']
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir']
        column_list.extend([BMMuser.xs8,])
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
    elif plotting_mode(mode) == 'xs' and kind == 'sead':
        column_list = ['I0', 'It', 'Ir']
        column_list.extend([BMMuser.xs1, BMMuser.xs2, BMMuser.xs3, BMMuser.xs4])
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
    elif plotting_mode(mode) == 'xs':
        table['xmu'] = (table[BMMuser.xs1]+table[BMMuser.xs2]+table[BMMuser.xs3]+table[BMMuser.xs4]) / table['I0']
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir']
        column_list.extend([BMMuser.xs1, BMMuser.xs2, BMMuser.xs3, BMMuser.xs4])
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
    elif plotting_mode(mode) == 'fluo':
        table['xmu'] = (table[BMMuser.dtc1] + table[BMMuser.dtc2] + table[BMMuser.dtc4]) / table['I0']
        if kind == '333':
            table['333_energy'] = table['dcm_energy']*3
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir',
                       BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4,
                       BMMuser.roi1, 'ICR1', 'OCR1',
                       BMMuser.roi2, 'ICR2', 'OCR2',
                       BMMuser.roi3, 'ICR3', 'OCR3',
                       BMMuser.roi4, 'ICR4', 'OCR4']
        if kind == '333':
            table['333_energy'] = table['dcm_energy']*3
            column_list[0] = '333_energy'
        #             en    en    dwti  xmu   io    it    ir    dtc1  dtc2  dtc3  dtc4  |----- 1 ------|  |----- 2 ------|  |----- 3 ------|  |----- 4 ------|  
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
        if BMMuser.detector == 1:
            #             en    en    dwti  xmu   io    it    ir    dtc1  |----- 1 ------|
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f\n"
            column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir',
                           BMMuser.dtc1, BMMuser.roi1, 'ICR1', 'OCR1',]

    else:
        if 'yield' in mode:     # yield is the primary measurement
            table['xmu'] = table['Iy'] / table['I0']
        elif 'ref' in mode:     # reference is the primary measurement
            table['xmu'] = numpy.log(table['It'] / table['Ir'])
        elif 'xs1' in mode:     # reference is the primary measurement
            table['xmu'] = table[BMMuser.xs8] / table['I0']
        elif 'xs' in mode:     # reference is the primary measurement
            table['xmu'] = (table[BMMuser.xs1]+table[BMMuser.xs2]+table[BMMuser.xs3]+table[BMMuser.xs4]) / table['I0']
        elif 'test' in mode:    # test scan, no log!
            table['xmu'] = table['I0']
        else:                   # transmission is the primary measurement
            table['xmu'] = numpy.log(table['I0'] / table['It'])
        if (kind == 'sead'):
            column_list = ['I0', 'It', 'Ir']
        else:
            column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'xmu', 'I0', 'It', 'Ir']
        if kind == '333':
            table['333_energy'] = table['dcm_energy']*3
            column_list[0] = '333_energy'
        template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f\n"
        if 'yield' in mode:
            column_list.append('Iy')
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
        elif 'xs1' in mode:
            column_list.extend([BMMuser.xs8,])
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
        elif 'xs' in mode:
            column_list.extend([BMMuser.xs1, BMMuser.xs2, BMMuser.xs3, BMMuser.xs4])
            template = "  %.3f  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f\n"
        if (kind == 'sead'):
            template = "  %.3f  %.6f  %.6f  %.6f\n"
    if kind == 'sead':
        column_list.insert(0, 'time')
    this = table.loc[:,column_list]

    for i in range(0,len(this)):
        datapoint = list(this.iloc[i])
        if kind == 'sead':
            ti = this.iloc[i, 0]
            st = this.iloc[0, 0]
            elapsed =  (ti.value - st.value)/10**9
            datapoint[0] = elapsed
        handle.write(template % tuple(datapoint))
        #handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
