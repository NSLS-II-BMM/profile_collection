


from bluesky.plan_stubs import null, sleep, mv, mvr
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import boxedtext

#from BMM import user_ns as user_ns_module
#user_ns = vars(user_ns_module)


class Linkam(Device):
    '''An ophyd wrapper around the Linkam T96 controller
    '''
    init = Cpt(EpicsSignal, 'INIT')
    model_array = Cpt(EpicsSignal, 'MODEL')
    serial_array = Cpt(EpicsSignal, 'SERIAL')
    stage_model_array = Cpt(EpicsSignal, 'STAGE:MODEL')
    stage_serial_array = Cpt(EpicsSignal, 'STAGE:SERIAL')
    firm_ver = Cpt(EpicsSignal, 'FIRM:VER')
    hard_ver = Cpt(EpicsSignal, 'HARD:VER')
    ctrllr_err = Cpt(EpicsSignal, 'CTRLLR:ERR')
    config = Cpt(EpicsSignal, 'CONFIG')
    status_code = Cpt(EpicsSignal, 'STATUS')
    stage_config = Cpt(EpicsSignal, 'STAGE:CONFIG')
    temp = Cpt(EpicsSignal, 'TEMP')
    disable = Cpt(EpicsSignal, 'DISABLE')
    dsc = Cpt(EpicsSignal, 'DSC')
    startheat = Cpt(EpicsSignal, 'STARTHEAT')
    RR_set = Cpt(EpicsSignal, 'RAMPRATE:SET')
    RR = Cpt(EpicsSignal, 'RAMPRATE')
    ramptime = Cpt(EpicsSignal, 'RAMPTIME')
    holdtime_set = Cpt(EpicsSignal, 'HOLDTIME:SET')
    holdtime = Cpt(EpicsSignal, 'HOLDTIME')
    SP_set = Cpt(EpicsSignal, 'SETPOINT:SET')
    SP = Cpt(EpicsSignal, 'SETPOINT')
    power = Cpt(EpicsSignal, 'POWER')
    lnp_speed = Cpt(EpicsSignal, 'LNP_SPEED')
    lnp_mode_set = Cpt(EpicsSignal, 'LNP_MODE:SET')
    lnp_speed_set = Cpt(EpicsSignal, 'LNP_SPEED:SET')

    
    @property
    def setpoint(self):
        return(self.SP.get())
    @setpoint.setter
    def setpoint(self, temperature):
        self.SP_set.put(float(temperature))
        
    @property
    def ramprate(self):
        return(self.RR.get())
    @ramprate.setter
    def ramprate(self, rate):
        self.RR_set.put(float(rate))
        
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
        
    def serial(self):
        return self.arr2word(self.serial_array.get())
    
    def model(self):
        return self.arr2word(self.model_array.get())
    
    def stage_model(self):
        return self.arr2word(self.stage_model_array.get())
    
    def stage_serial(self):
        return self.arr2word(self.stage_serial_array.get())

    def firmware_version(self):
        return self.arr2word(self.firm_ver.get())

    def hardware_version(self):
        return self.arr2word(self.hard_ver.get())

    def status(self):
        text = f'\nCurrent temperature = {self.temp.get():.1f}, setpoint = {self.SP.get():.1f}\n\n'
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
            
        boxedtext(f'Linkam {self.model()}, stage {self.stage_model()}', text, 'brown', width = 45)

from BMM.macrobuilder import BMMMacroBuilder

class LinkamMacroBuilder(BMMMacroBuilder):
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM glancing angle
    stage.

    Examples
    --------
    >>> lmb = LinkamMacroBuilder()
    >>> lmb.spreadsheet('wheel1.xlsx')
    >>> lmb.write_macro()

    '''
        
    def _write_macro(self):
        '''Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of line to move to the
        correct spinner, lines to find or move to the center-aligned
        location in pitch and Y, lines to move to and from the correct
        glancing angle value, a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.
        '''
        element, edge, focus = (None, None, None)
        for m in self.measurements:

            if m['default'] is True:
                element = m['element']
                edge    = m['edge']
                continue
            if self.skip_row(m) is True:
                continue

            #######################################
            # default element/edge(/focus) values #
            #######################################
            for k in ('element', 'edge'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]

            ############################
            # sample and slit movement #
            ############################
            self.content += self.tab + 'yield from linkam.on_plan()\n'
            self.content += self.tab + f'yield from mv(linkam.SP_set, {m["temperature"]:.1f})\n'
            if m['samplex'] is not None:
                self.content += self.tab + f'yield from mv(xafs_x, {m["samplex"]:%.3f})\n'
            if m['sampley'] is not None:
                self.content += self.tab + f'yield from mv(xafs_y, {m["sampley"]:%.3f})\n'
            if m['detectorx'] is not None:
                self.content += self.tab + f'yield from mv(xafs_det, {m["detectorx"]:%.2f})\n'

            
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

            ########################################
            # approximate time cost of this sample #
            ########################################
            self.estimate_time(m, element, edge)
            

        if self.close_shutters:
            self.content += self.tab + 'if not dryrun:\n'
            self.content += self.tab + '    BMMuser.running_macro = False\n'
            self.content += self.tab + '    BMM_clear_suspenders()\n'
            self.content += self.tab + '    yield from shb.close_plan()\n'


    def get_keywords(self, row, defaultline):
        '''Instructions for parsing spreadsheet columns into keywords.

        arguments
        ---------
        row : contents of a row as read by openpyxl, i.e. ws.rows
        defaultline : True only if this row contains the default
        parameters, i.e. the green row

        This must return a dictionary.  The dictionary keys are the
        keywords related to the column labels from the spreadsheet,
        the values are cell contents, possibly reduced to a specific
        type.

        '''
        this = {'default':     defaultline,
                'temperature': float(row[1].value),      # sample location
                'measure':     self.truefalse(row[2].value),  # filename and visualization
                'filename':    row[3].value,
                'nscans':      row[4].value,
                'start':       row[5].value,
                'mode':        row[6].value,
                'element':     row[7].value,      # energy range
                'edge':        row[8].value,
                'focus':       row[9].value,
                'sample':      row[10].value,     # scan metadata
                'prep':        row[11].value,
                'comment':     row[12].value,
                'bounds':      row[13].value,     # scan parameters
                'steps':       row[14].value,
                'times':       row[15].value,
                'samplex':     row[16].value,     # other motors
                'sampley':     row[17].value,
                'detectorx':   row[18].value,
                'snapshots':   self.truefalse(row[19].value),  # flags
                'htmlpage':    self.truefalse(row[20].value),
                'usbstick':    self.truefalse(row[21].value),
                'bothways':    self.truefalse(row[22].value),
                'channelcut':  self.truefalse(row[23].value),
                'ththth':      self.truefalse(row[24].value),
                'url':         row[25].value,
                'doi':         row[26].value,
                'cif':         row[27].value, }
        return this

        
