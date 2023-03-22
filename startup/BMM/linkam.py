
from bluesky.plan_stubs import null, sleep, mv, mvr
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device, PVPositioner
from ophyd.signal import DerivedSignal

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import boxedtext

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


class AtSetpoint(DerivedSignal):
    '''A signal that does bit-wise arithmetic on the Linkam's status code'''
    def __init__(self, parent_attr, *, parent=None, **kwargs):
        code_signal = getattr(parent, parent_attr)
        super().__init__(derived_from=code_signal, parent=parent, **kwargs)

    def inverse(self, value):
        if int(value) & 2 == 2:
            return 1
        else:
            return 0

    def forward(self, value):
        return value

    # def describe(self):
    #     desc = super().describe()
    #     desc[self.name]['units'] = 'eV'
    #     return desc

    
class Linkam(PVPositioner):
    '''An ophyd wrapper around the Linkam T96 controller

    At BMM, communication to the Linkam is through Moxa 7
    (xf06bm-tsrv7, 10.68.42.77) where port 1 is connected to the RS232
    port on the Linkam T96 controller.
    '''

    ## following https://blueskyproject.io/ophyd/positioners.html#pvpositioner
    readback = Cpt(EpicsSignalRO, 'TEMP')
    setpoint = Cpt(EpicsSignal, 'SETPOINT:SET')
    status_code = Cpt(EpicsSignal, 'STATUS')
    done = Cpt(AtSetpoint, parent_attr = 'status_code')

    ## all the rest of the Linkam signals
    init = Cpt(EpicsSignal, 'INIT')
    model_array = Cpt(EpicsSignal, 'MODEL')
    serial_array = Cpt(EpicsSignal, 'SERIAL')
    stage_model_array = Cpt(EpicsSignal, 'STAGE:MODEL')
    stage_serial_array = Cpt(EpicsSignal, 'STAGE:SERIAL')
    firm_ver = Cpt(EpicsSignal, 'FIRM:VER')
    hard_ver = Cpt(EpicsSignal, 'HARD:VER')
    ctrllr_err = Cpt(EpicsSignal, 'CTRLLR:ERR')
    config = Cpt(EpicsSignal, 'CONFIG')
    stage_config = Cpt(EpicsSignal, 'STAGE:CONFIG')
    disable = Cpt(EpicsSignal, 'DISABLE')
    dsc = Cpt(EpicsSignal, 'DSC')
    RR_set = Cpt(EpicsSignal, 'RAMPRATE:SET')
    RR = Cpt(EpicsSignal, 'RAMPRATE')
    ramptime = Cpt(EpicsSignal, 'RAMPTIME')
    startheat = Cpt(EpicsSignal, 'STARTHEAT')
    holdtime_set = Cpt(EpicsSignal, 'HOLDTIME:SET')
    holdtime = Cpt(EpicsSignal, 'HOLDTIME')
    power = Cpt(EpicsSignalRO, 'POWER')
    lnp_speed = Cpt(EpicsSignal, 'LNP_SPEED')
    lnp_mode_set = Cpt(EpicsSignal, 'LNP_MODE:SET')
    lnp_speed_set = Cpt(EpicsSignal, 'LNP_SPEED:SET')

            
    def on(self):
        self.startheat.put(1)

    def off(self):
        self.startheat.put(0)
    
    def on_plan(self):
        return(yield from mv(self.startheat, 1))

    def off_plan(self):
        return(yield from mv(self.startheat, 0))

    def arr2word(self, lst):
        word = ''
        for l in lst[:-1]:
            word += chr(l)
        return word
        
    @property
    def serial(self):
        return self.arr2word(self.serial_array.get())

    @property
    def model(self):
        return self.arr2word(self.model_array.get())
    
    @property
    def stage_model(self):
        return self.arr2word(self.stage_model_array.get())
    
    @property
    def stage_serial(self):
        return self.arr2word(self.stage_serial_array.get())

    @property
    def firmware_version(self):
        return self.arr2word(self.firm_ver.get())

    @property
    def hardware_version(self):
        return self.arr2word(self.hard_ver.get())

    def status(self):
        text = f'\nCurrent temperature = {self.readback.get():.1f}, setpoint = {self.setpoint.get():.1f}\n\n'
        code = int(self.status_code.get())
        if code & 1:
            text += error_msg('Error        : yes') + '\n'
        else:
            text += 'Error        : no\n'
        if code & 2:
            text += go_msg('At setpoint  : yes') + '\n'
        else:
            text += 'At setpoint  : no\n'
        if code & 4:
            text += go_msg('Heater       : on') + '\n'
        else:
            text += 'Heater       : off\n'
        if code & 8:
            text += go_msg('Pump         : on') + '\n'
        else:
            text += 'Pump         : off\n'
        if code & 16:
            text += go_msg('Pump Auto    : yes') + '\n'
        else:
            text += 'Pump Auto    : no\n'
            
        boxedtext(f'Linkam {self.model}, stage {self.stage_model}', text, 'brown', width = 48)

    def dossier_entry(self):
        thistext  =  '	    <div id="boxinst">\n'
        thistext +=  '	      <h3>Instrument: Linkam stage</h3>\n'
        thistext +=  '	      <ul>\n'
        thistext += f'               <li><b>Temperature:</b> {self.readback.get():.1f} C</li>\n'
        thistext += f'               <li><b>Set point:</b> {self.setpoint.get():.1f} C</li>\n'
        thistext += f'               <li><b>Heater power:</b> {self.power.get():.1f}%</li>\n'
        thistext +=  '	      </ul>\n'
        thistext +=  '	    </div>\n'
        return thistext
        
        
        
from BMM.macrobuilder import BMMMacroBuilder

class LinkamMacroBuilder(BMMMacroBuilder):
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS using the Linkam stage.

    Examples
    --------
    >>> lmb = LinkamMacroBuilder()
    >>> lmb.spreadsheet('linkam.xlsx')
    >>> lmb.write_macro()

    '''
        
    def _write_macro(self):
        '''Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of lines to change the
        temperature, lines to move sample and detector to the correct
        positions (if needed), a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.

        '''
        element, edge, focus = (None, None, None)
        settle_time, ramp_time = 0,0
        previous = 25
        
        self.content += self.tab + 'yield from mv(linkam.setpoint, linkam.readback.get())\n\n'
        self.content += self.tab + 'yield from linkam.on_plan()\n'
        self.content += self.tab + 'yield from mv(busy, 15)\n'

        for m in self.measurements:

            if m['default'] is True:
                element     = m['element']
                edge        = m['edge']
                temperature = m['temperature']
                continue
            if m['temperature'] is None:
                continue
            if self.skip_row(m) is True:
                continue

            #######################################
            # default element/edge(/focus) values #
            #######################################
            for k in ('element', 'edge', 'focus'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]
            if m['settle'] == 0:
                m['settle'] = self.measurements[0]['settle']

            ################################
            # change temperature is needed #
            ################################
            if m['temperature'] != temperature:
                if self.check_temp(user_ns['linkam'], m['temperature']) is False: return(False)
                self.content += self.tab + f"report('== Moving to temperature {m['temperature']:.1f}C', slack=True)\n"
                self.content += self.tab +  'linkam.settle_time = 10\n'
                self.content += self.tab + f'yield from mv(linkam, {m["temperature"]:.1f})\n'
                self.content += self.tab + f"report('== Holding at temperature {m['temperature']:.1f}C for {m['settle']} seconds', slack=True)\n"
                self.content += self.tab + f'yield from mv(busy, {m["settle"]:.1f})\n'
                temperature = m['temperature']
                settle_time += m["settle"]
                ramp_time += (temperature - previous) / user_ns['linkam'].RR.get()
                previous = temperature

            ############################
            # sample and slit movement #
            ############################           
            if m['samplex'] is not None:
                if self.check_limit(user_ns['xafs_x'], m['samplex']) is False: return(False)
                self.content += self.tab + f'yield from mv(xafs_x, {m["samplex"]:.3f})\n'
            if m['sampley'] is not None:
                if self.check_limit(user_ns['xafs_y'], m['sampley']) is False: return(False)
                self.content += self.tab + f'yield from mv(xafs_y, {m["sampley"]:.3f})\n'
            if m['detectorx'] is not None:
                if self.check_limit(user_ns['xafs_det'], m['detectorx']) is False: return(False)
                self.content += self.tab + f'yield from mv(xafs_det, {m["detectorx"]:.2f})\n'

            
            ##########################
            # change edge, if needed #
            ##########################
            focus = False
            if m['focus'] == 'focused':
                focus = True
            if self.do_first_change is True:
                self.content += self.tab + 'yield from change_edge(\'%s\', edge=\'%s\', focus=%r)\n' % (m['element'], m['edge'], focus)
                self.do_first_change = False
                self.totaltime += 4
                
            elif m['element'] != element or m['edge'] != edge: # focus...
                element = m['element']
                edge    = m['edge']
                self.content += self.tab + 'yield from change_edge(\'%s\', edge=\'%s\', focus=%r)\n' % (m['element'], m['edge'], focus)
                self.totaltime += 4
                
            else:
                if self.verbose:
                    self.content += self.tab + '## staying at %s %s\n' % (m['element'], m['edge'])
                pass

            ######################################
            # measure XAFS, then close all plots #
            ######################################
            command = self.tab + 'yield from xafs(\'%s.ini\'' % self.basename
            for k in m.keys():
                ## skip cells with macro-building parameters that are not INI parameters
                if self.skip_keyword(k):
                    continue
                ## skip element & edge if they are same as default
                elif k in ('element', 'edge'):
                    if m[k] == self.measurements[0][k]:
                        continue
                ## skip cells with only whitespace
                if type(m[k]) is str and len(m[k].strip()) == 0:
                    m[k] = None
                ## if a cell has data, put it in the argument list for xafs()
                if m[k] is not None:
                    if k == 'filename':
                        fname = self.make_filename(m)
                        command += f', filename=\'{fname}\''
                    elif type(m[k]) is int:
                        command += ', %s=%d' % (k, m[k])
                    elif type(m[k]) is float:
                        command += ', %s=%.3f' % (k, m[k])
                    else:
                        command += ', %s=\'%s\'' % (k, m[k])
            command += ')\n'
            self.content += command
            self.content += self.tab + 'close_last_plot()\n\n'
            #self.content += self.tab + 'yield from linkam.off_plan()\n\n'

            ########################################
            # approximate time cost of this sample #
            ########################################
            self.estimate_time(m, element, edge)

        print(whisper(f'XAS time:      about {self.totaltime/60:.1f} hours'))
        print(whisper(f'ramp time:     about {ramp_time:.1f} minutes'))
        print(whisper(f'settling time: about {settle_time/60:.1f} minutes'))
        self.totaltime = self.totaltime + (settle_time / 60) + ramp_time
        if self.close_shutters:
            self.content += self.tab + 'if not dryrun:\n'
            self.content += self.tab + '    BMMuser.running_macro = False\n'
            self.content += self.tab + '    BMM_clear_suspenders()\n'
            self.content += self.tab + '    yield from shb.close_plan()\n'
        return(True)


    def get_keywords(self, row, defaultline):
        '''Instructions for parsing spreadsheet columns into keywords.

        arguments
        ---------
        row : contents of a row as read by openpyxl, i.e. ws.rows
        defaultline : True only if this row contains the default
        parameters, i.e. the green row

        This must return a dictionary.  The dictionary keys are the
        keywords related to the column labels from the spreadsheet,
        the values are cell contents, possibly coerced to a specific
        type.

        '''
        this = {'default':     defaultline,
                'temperature': row[1].value,          # measurement temperature
                'settle':      self.nonezero(row[2].value),  # temperature settling time
                'measure':     self.truefalse(row[3].value, 'measure'), # filename and visualization
                'filename':    str(row[4].value),
                'nscans':      row[5].value,
                'start':       row[6].value,
                'mode':        row[7].value,
                'element':     row[8].value,      # energy range
                'edge':        row[9].value,
                'focus':       row[10].value,
                'sample':      self.escape_quotes(str(row[11].value)),     # scan metadata
                'prep':        self.escape_quotes(str(row[12].value)),
                'comment':     self.escape_quotes(str(row[13].value)),
                'bounds':      row[14].value,     # scan parameters
                'steps':       row[15].value,
                'times':       row[16].value,
                'samplex':     row[17].value,     # other motors
                'sampley':     row[18].value,
                'detectorx':   row[19].value,
                'snapshots':   self.truefalse(row[20].value, 'snapshots' ),  # flags
                'htmlpage':    self.truefalse(row[21].value, 'htmlpage'  ),
                'usbstick':    self.truefalse(row[22].value, 'usbstick'  ),
                'bothways':    self.truefalse(row[23].value, 'bothways'  ),
                'channelcut':  self.truefalse(row[24].value, 'channelcut'),
                'ththth':      self.truefalse(row[25].value, 'ththth'    ),
                'url':         row[26].value,
                'doi':         row[27].value,
                'cif':         row[28].value, }
        return this

        
