
from bluesky.plan_stubs import sleep, mv, mvr, null
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

import os, re
from openpyxl import load_workbook
import configparser
import numpy

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import isfloat, present_options
from BMM.logging        import report
from BMM.macrobuilder   import BMMMacroBuilder
from BMM.periodictable  import PERIODIC_TABLE, edge_energy
from BMM.xafs_functions import conventional_grid, sanitize_step_scan_parameters

from IPython import get_ipython
user_ns = get_ipython().user_ns

class GlancingAngle(Device):
    spinner1 = Cpt(EpicsSignal, 'OutPt08:Data-Sel')
    spinner2 = Cpt(EpicsSignal, 'OutPt09:Data-Sel')
    spinner3 = Cpt(EpicsSignal, 'OutPt10:Data-Sel')
    spinner4 = Cpt(EpicsSignal, 'OutPt11:Data-Sel')
    spinner5 = Cpt(EpicsSignal, 'OutPt12:Data-Sel')
    spinner6 = Cpt(EpicsSignal, 'OutPt13:Data-Sel')
    spinner7 = Cpt(EpicsSignal, 'OutPt14:Data-Sel')
    spinner8 = Cpt(EpicsSignal, 'OutPt15:Data-Sel')
    #rotation

    spin = True
    home = 0
    garot = user_ns['xafs_garot']
    
    def current(self):
        pos = self.garot.position
        cur = pos % 360
        here = (9-round(cur/45)) % 8
        if here == 0:
            here = 8
        return here

    def reset(self):
        '''Return glancing angle stage to spinner 1'''
        yield from self.alloff_plan()
        yield from mv(self.garot, self.home)
        report('Returned to spinner 1 at %d degrees and turned off all spinners' % self.home, level='bold')
        
    def valid(self, number=None):
        if number is None:
            return False
        if type(number) is not int:
            return False
        if number < 1 or number > 8:
            return False
        return True
        
    def on(self, number):
        if self.spin is False:
            print(warning_msg('The spinners are currently disabled.  do "ga.spin = True" to re-enable.'))
            return
        if not self.valid(number):
            print(error_msg('The fans are numbered from 1 to 8'))
            return
        this = getattr(self, f'spinner{number}')
        this.put(1)
    def off(self, number=None):
        if number is None:
            self.alloff()
            return
        if not self.valid(number):
            print(error_msg('The fans are numbered from 1 to 8'))
            return
        this = getattr(self, f'spinner{number}')
        this.put(0)
        
    def alloff(self):
        for i in range(1,9):
            self.off(i)
    def alloff_plan(self):
        RE = user_ns['RE']
        save = RE.msg_hook
        RE.msg_hook = None
        for i in range(1,9):
            this = getattr(self, f'spinner{i}')
            yield from mv(this, 0)
        RE.msg_hook = save
            
    def to(self, number):
        if not self.valid(number):
            print(error_msg('The fans are numbered from 1 to 8'))
            yield from null()
            return
        yield from self.alloff_plan()
        distance = number - self.current()
        if distance > 4:
            distance = distance - 8
        elif distance < -4:
            distance = 8 + distance
        angle = -45*distance
        yield from mvr(self.garot, angle)
        if self.spin is True:
            this = getattr(self, f'spinner{number}')
            yield from mv(this, 1)


class PinWheelMacroBuilder(BMMMacroBuilder):
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM glancing angle
    stage.

    Examples
    --------
    >>> mb = PinWheelMacroBuilder()
    >>> mb.spreadsheet('wheel1.xlsx')
    >>> mb.write_macro()

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
            for k in ('element', 'edge', 'method', 'focus', 'spin', 'angle'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]

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

            #######################################
            # sample alignment and glancing angle #
            #######################################
            self.content += self.tab + f'ga.spin = {m["spin"]}\n'
            self.content += self.tab + f'yield from ga.to({m["slot"]})\n'
            if m['method'].lower() == 'automatic':
                self.content += self.tab + 'yield from align_ga()\n'
            else:
                if m['samplep'] is not None:
                    self.content += self.tab + f'yield from mv(xafs_pitch, {m["samplep"]})\n'
                if m['sampley'] is not None:
                    self.content += self.tab + f'yield from mv(xafs_y, {m["sampley"]})\n'
            self.content += self.tab + f'yield from mvr(xafs_pitch, {m["angle"]})\n'

                    
            ############################################################
            # measure XAFS, then return to 0 pitch and close all plots #
            ############################################################
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
            self.content += self.tab + f'yield from mvr(xafs_pitch, {-1*m["angle"]})\n'
            self.content += self.tab + 'close_last_plot()\n\n'


            ########################################
            # approximate time cost of this sample #
            ########################################
            self.estimate_time(m, element, edge)
            

        if self.close_shutters:
            self.content += self.tab + 'if not dryrun:\n'
            self.content += self.tab + '    yield from shb.close_plan()\n'

            


    def get_keywords(self, row, defaultline):
        '''Instructions for parsing spreadsheet columns into keywords.

        arguments
        ---------
        row : contents of a row as read by openpyxl, i.e. ws.rows
        defaultline : True only if this row contains the default parameters, i.e. green row

        This must return a dictionary.  The dictionary keys are the
        keywords related to the column labels from the spreadsheet,
        the values are cell contents, possibly reduced to a specific
        type.

        '''
        this = {'default' :   defaultline,
                'slot':       row[1].value,      # sample location
                'measure':    self.truefalse(row[2].value),  # filename and visualization
                'filename':   row[3].value,
                'nscans':     row[4].value,
                'start':      row[5].value,
                'spin':       self.truefalse(row[6].value),
                'element':    row[7].value,      # energy range
                'edge':       row[8].value,
                'focus':      row[9].value,
                'angle':      row[10].value,
                'sample':     row[11].value,     # scan metadata
                'prep':       row[12].value,
                'comment':    row[13].value,
                'bounds':     row[14].value,     # scan parameters
                'steps':      row[15].value,
                'times':      row[16].value,
                'method':     row[17].value,
                'samplep':    row[18].value,     # other motors 
                'sampley':    row[19].value,
                'snapshots':  self.truefalse(row[20].value), # flags
                'htmlpage':   self.truefalse(row[21].value),
                'usbstick':   self.truefalse(row[22].value),
                'bothways':   self.truefalse(row[23].value),
                'channelcut': self.truefalse(row[24].value),
                'ththth':     self.truefalse(row[25].value),
                'url':        row[26].value,
                'doi':        row[27].value,
                'cif':        row[28].value, }
        return this

