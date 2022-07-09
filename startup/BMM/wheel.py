import sys, os.path, re
#import pprint
#pp = pprint.PrettyPrinter(indent=4)
from openpyxl import load_workbook
import configparser
import numpy

from bluesky.plan_stubs import null, sleep, mv, mvr

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import isfloat, present_options
from BMM.macrobuilder   import BMMMacroBuilder
from BMM.motors         import EndStationEpicsMotor
from BMM.periodictable  import PERIODIC_TABLE, edge_energy
from BMM.logging        import report
from BMM.xafs_functions import conventional_grid
from BMM.workspace      import rkvs

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

class WheelMotor(EndStationEpicsMotor):
    '''Motor class for BMM sample wheels.
    
    These wheels have 24 slots, spaced 15 degrees apart.

    Methods
    -------
    current_slot() :
        return the current slot number, even if the wheel has rotated many times
    set_slot(n) :
        move to the given slot number, taking care to go the shorter way
    '''
    if rkvs.get('BMM:wheel:outer') is None:
        outer_position = 0
    else:
        outer_position   = float(rkvs.get('BMM:wheel:outer'))
    inner_position   = outer_position + 26.0
    def current_slot(self, value=None):
        '''Return the current slot number for a sample wheel.'''
        if value is not None:
            angle = round(value)
        else:
            angle = round(self.user_readback.get())
        this = round((-1*self.slotone-15+angle) / (-15)) % 24
        if this == 0: this = 24
        return this

    def reset(self):
        '''Return a sample wheel to slot 1'''
        yield from mv(self, self.slotone)
        report('Returned to sample wheel slot 1 at %d degrees' % self.slotone, level='bold')

    def angle_from_current(self, n):
        '''Return the angle from the current position to the target'''
        if type(n) is not int:
            print(error_msg('Slots numbers must be integers between 1 and 24 (argument was %s)' % type(n)))
            return(0)
        if n<1 or n>24:
            print(error_msg('Slots are numbered from 1 to 24'))
            return(0)

        current = self.current_slot()
        distance = n - current
        if distance > 12:
            distance = distance - 24
        elif distance < -12:
            distance = 24 + distance
        angle = -15*distance
        return angle
        
    def set_slot(self, n):
        '''Move to a numbered slot on a sample wheel.'''
        if type(n) is not int:
            print(error_msg('Slots numbers must be integers between 1 and 24 (argument was %s)' % type(n)))
            return(yield from null())
        if n<1 or n>24:
            print(error_msg('Slots are numbered from 1 to 24'))
            return(yield from null())
        angle = self.angle_from_current(n)
        yield from mvr(self, angle)
        report('Arrived at sample wheel slot %d' % n, level='bold')

    def slot_number(self, target=None):
        try:
            target = target.capitalize()
            slot = self.content.index(target) + 1
            return slot
        except:
            return self.current_slot()

        
    def position_of_slot(self, target):
        if type(target) is int:
            angle = self.angle_from_current(target)
        elif type(target) is str:
            target = self.slot_number(target.capitalize())
            angle = self.angle_from_current(target)
        return(self.user_readback.get()+angle)

    def recenter(self):
        here = self.user_readback.get()
        center = round(here / 15) * 15
        yield from mv(self, center)
        print(whisper('recentered %s to %.1f' % (self.name, center)))

    def in_place(self):
        #user_ns['wmb'].outer_position = user_ns['xafs_x'].position
        #user_ns['wmb'].inner_position = user_ns['wmb'].outer_position + 26
        self.outer_position = user_ns['xafs_x'].position
        self.inner_position = self.outer_position + 26
        rkvs.set('BMM:wheel:outer', self.outer_position)

    def inner(self):
        yield from mv(user_ns['xafs_x'], self.inner_position)

    def outer(self):
        yield from mv(user_ns['xafs_x'], self.outer_position)

    def slot_ring(self):
        if 'double' in user_ns['BMMuser'].instrument:
            if abs(user_ns['xafs_x'].position - self.inner_position) < 1.0:
                return 'inner'
            else:
                return 'outer'
        else:
            return 'outer'

    def dossier_entry(self):
        thistext  =  '	    <div id="boxinst">\n'
        thistext +=  '	      <h3>Instrument: Ex situ sample wheel</h3>\n'
        thistext +=  '	      <ul>\n'
        thistext += f'               <li><b>Slot number:</b> {self.current_slot()}</li>\n'
        thistext += f'               <li><b>Ring:</b> {self.slot_ring()}</li>\n'
        thistext +=  '	      </ul>\n'
        thistext +=  '	    </div>\n'
        return thistext

        


def reference(target=None):
    xafs_ref = user_ns['xafs_ref']
    if target is None:
        print('Not moving reference wheel.')
        return(yield from null())
    if type(target) is int:
        if target < 1 or target > 24:
            print('An integer reference target must be between 1 and 24 (%d)' % target)
            return(yield from null())
        else:
            yield from xafs_ref.set_slot(target)
            return
    try:
        target = target.capitalize()
        slot = xafs_ref.content.index(target) + 1
        yield from xafs_ref.set_slot(slot)
    except:
        print('Element %s is not on the reference wheel.' % target)
        

def show_reference_wheel():
    xafs_ref = user_ns['xafs_ref']
    wheel = xafs_ref.content.copy()
    this  = xafs_ref.current_slot() - 1
    #wheel[this] = go_msg(wheel[this])
    text = 'Foil wheel:\n'
    text += bold_msg('    1      2      3      4      5      6      7      8      9     10     11     12\n')
    text += ' '
    for i in range(12):
        if i==this:
            text += go_msg('%4.4s' % str(wheel[i])) + '   '
        else:
            text += '%4.4s' % str(wheel[i]) + '   '
    text += '\n'
    text += bold_msg('   13     14     15     16     17     18     19     20     21     22     23     24\n')
    text += ' '
    for i in range(12, 24):
        if i==this:
            text += go_msg('%4.4s' % str(wheel[i])) + '   '
        else:
            text += '%4.4s' % str(wheel[i]) + '   '
    text += '\n'
    return(text)

class WheelMacroBuilder(BMMMacroBuilder):
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM wheel.

    Examples
    --------
    >>> mb = MacroBuilder()
    >>> mb.spreadsheet('wheel1.xlsx')
    >>> mb.write_macro()
    '''

    def _write_macro(self):
        '''Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of line to move to the
        correct wheel slot, a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.  

        Finally, write out the master INI and macro python files.
        '''
        element, edge, focus, slot = (None, None, None, None)

        if self.nreps > 1:
            self.content = self.tab + f'for reps in range({self.nreps}):\n\n'
            self.tab = ' '*12

        for m in self.measurements:

            if m['default'] is True:
                element = m['element']
                edge    = m['edge']
                slot    = 0
                continue
            if self.skip_row(m) is True:
                continue

            #######################################
            # default element/edge(/focus) values #
            #######################################
            for k in ('element', 'edge', 'focus'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]

            ############################
            # sample and slit movement #
            ############################
            if m['slot'] != slot:
                self.content += self.tab + 'yield from slot(%d)\n' % m['slot']
                slot = m['slot']
            if 'ring' in m:
                #here = user_ns['xafs_det'].position
                #if here < 150:
                #    self.content += self.tab + 'yield from mvr(xafs_det, 20)\n'
                if m['ring'].lower() == 'inner':
                    self.content += self.tab + f'yield from xafs_wheel.inner() # inner ring\n'
                else:
                    self.content += self.tab + f'yield from xafs_wheel.outer() # outer ring\n'
                #if here < 150:
                #    self.content += self.tab + f'yield from mv(xafs_det, {here:.3f})\n'
            if m['samplex'] is not None:
                self.content += self.tab + 'yield from mv(xafs_x, %.3f)\n' % m['samplex']
            if m['sampley'] is not None:
                self.content += self.tab + 'yield from mv(xafs_y, %.3f)\n' % m['sampley']
            if m['slitwidth'] is not None:
                self.content += self.tab + 'yield from mv(slits3.hsize, %.2f)\n' % m['slitwidth']
            if m['detectorx'] is not None:
                self.content += self.tab + 'yield from mv(xafs_det, %.2f)\n' % m['detectorx']

            
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
                    #continue
                    m[k] = None
                ## if a cell has data, put it in the argument list for xafs()
                if m[k] is not None and m[k] != '':
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
            if element is None:
                element = self.measurements[0]['element']
            if edge is None:
                edge = self.measurements[0]['edge']
            self.estimate_time(m, element, edge)
            
        if self.nreps > 1:
            self.tab = ' ' * 8
            
        if self.close_shutters:
            self.content += self.tab + 'if not dryrun:\n'
            self.content += self.tab + '    BMMuser.running_macro = False\n'
            self.content += self.tab + '    BMM_clear_suspenders()\n'
            self.content += self.tab + '    yield from shb.close_plan()\n'



    def get_keywords(self, row, defaultline):
        plus = 0
        if self.double is True:  # make room for column denoting inner and outer ring
            plus = 1
        this = {'default' :   defaultline,
                'slot':       row[1].value,      # sample location
                'measure':    self.truefalse(row[2+plus].value, 'measure'),  # filename and visualization
                'filename':   row[3+plus].value,
                'nscans':     row[4+plus].value,
                'start':      row[5+plus].value,
                'mode':       row[6+plus].value,
                #'e0':         row[7].value,      
                'element':    row[7+plus+self.offset].value,      # energy range
                'edge':       row[8+plus+self.offset].value,
                'focus':      row[9+plus+self.offset].value,
                'sample':     self.escape_quotes(row[10+plus+self.offset].value),     # scan metadata
                'prep':       self.escape_quotes(row[11+plus+self.offset].value),
                'comment':    self.escape_quotes(row[12+plus+self.offset].value),
                'bounds':     row[13+plus+self.offset].value,     # scan parameters
                'steps':      row[14+plus+self.offset].value,
                'times':      row[15+plus+self.offset].value,
                'samplex':    row[16+plus+self.offset].value,     # other motors 
                'sampley':    row[17+plus+self.offset].value,
                'slitwidth':  row[18+plus+self.offset].value,
                'detectorx':  row[19+plus+self.offset].value,
                'snapshots':  self.truefalse(row[20+plus+self.offset].value, 'snapshots' ), # flags
                'htmlpage':   self.truefalse(row[21+plus+self.offset].value, 'htmlpage'  ),
                'usbstick':   self.truefalse(row[22+plus+self.offset].value, 'usbstick'  ),
                'bothways':   self.truefalse(row[23+plus+self.offset].value, 'bothways'  ),
                'channelcut': self.truefalse(row[24+plus+self.offset].value, 'channelcut'),
                'ththth':     self.truefalse(row[25+plus+self.offset].value, 'ththth'    ),
                'url':        row[26+plus+self.offset].value,
                'doi':        row[27+plus+self.offset].value,
                'cif':        row[28+plus+self.offset].value, }
        if self.double is True:
            this['ring'] = row[2].value
        return this
                         
            
