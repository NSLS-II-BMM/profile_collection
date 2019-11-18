
import sys, os.path, re
#import pprint
#pp = pprint.PrettyPrinter(indent=4)
from openpyxl import load_workbook
import configparser

run_report(__file__)


class WheelMotor(EndStationEpicsMotor):
    '''Motor class for BMM sample wheels.
    
    These wheels have 24 slots, spaced 15 degrees apart.

    current_slot():
       return the current slot number, even if the wheel has rotated many times

    set_slot(n):
       move to the given slot number, taking care to go the shorter way
    '''
    def current_slot(self, value=None):
        '''Return the current sample wheel slot number.'''
        if value is not None:
            angle = round(value)
        else:
            angle = round(xafs_wheel.user_readback.value)
        this = round((-1*self.slotone-15+angle) / (-15)) % 24
        if this == 0: this = 24
        return this

    def reset(self):
        '''Return the wheel to slot 1'''
        yield from mv(self, self.slotone)
        report('Returned to sample wheel slot 1 at %d degrees' % self.slotone, 'bold')
    
    def set_slot(self, n):
        '''Move to a numbered slot on the sample wheel.'''
        if type(n) is not int:
            print(error_msg('Slots numbers must be integers between 1 and 24 (argument was %s)' % type(n)))
            return(yield from null())
        if n<1 or n>24:
            print(error_msg('Slots are numbered from 1 to 24'))
            return(yield from null())

        current = self.current_slot()
        distance = n - current
        if distance > 12:
            distance = distance - 24
        elif distance < -12:
            distance = 24 + distance
        angle = -15*distance
        yield from mvr(xafs_wheel, angle)
        report('Arrived at sample wheel slot %d' % n, 'bold')

xafs_wheel = xafs_rotb  = WheelMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_wheel.slotone = -30        # the angular position of slot #1
xafs_wheel.user_offset.put(-2.079)
slot = xafs_wheel.set_slot

## reference foil wheel will be something like this:
# xafs_wheel.content = ['Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As',
#                       'Se', 'Br', 'Sr', 'Y',  'Nb', 'Mo', 'Hf', 'W',  'Re'  'Pt', 'Au', 'Pb']
#
# others: Zr, Rb, Ta, Hg, Ru, Bi, Cs, Ba, La, Ce to Lu (14)
#
# too low (H-Sc): 21
# noble gases: 4
# Rh to I: 9
# radioactive (Tc, Po, At, Fr - U): 9 (Tc, U, and Th could be part of the experiment)
#
# available = 47, unavailable = 45
#
# then,
#   try:
#      sl = xafs_wheel.content.index[elem] + 1
#      yield from reference_slot(sl)
#   except:
#      # don't move reference wheel


def setup_wheel():
    yield from mv(xafs_x, -119.7, xafs_y, 112.1, xafs_wheel, 0)
    


class WheelMacroBuilder():
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM wheel.

    Example:
       mb = MacroBuilder()
       mb.spreadsheets('wheel1.xlsx')
       mb.write_macro()
    '''
    def __init__(self):
        self.basename     = None
        self.folder       = BMMuser.folder

        self.source       = None
        self.wb           = None
        self.ws           = None
        self.measurements = list()
        self.ini          = None
        self.macro        = None

        self.tab          = '        '
        self.content      = ''
        self.do_first_change = False

    def spreadsheet(self, spreadsheet):
        '''Read the spreadsheet and set several filenames based on the name of the spreadsheet.'''
        self.source   = os.path.join(self.folder, spreadsheet)
        self.basename = os.path.splitext(spreadsheet)[0]
        self.wb       = load_workbook(self.source, read_only=True);
        self.ws       = self.wb.active
        self.ini      = os.path.join(self.folder, self.basename+'.ini')
        self.tmpl     = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup', 'wheelmacro.tmpl')
        self.macro    = os.path.join(self.folder, self.basename+'_macro.py')
        self.measurements = list()
        self.read_spreadsheet()
        
    def truefalse(self, value):
        '''Interpret certain strings from the spreadsheet as True/False'''
        if value is None:
            return self.measurements[0]['measure']
        if str(value).lower() == '=true()':
            return True
        elif str(value).lower() == 'true':
            return True
        elif str(value).lower() == 'yes':
            return True
        else:
            return False

    def read_spreadsheet(self):
        '''Slurp up the content of the spreadsheet and write the default control file
        '''
        print('Reading spreadsheet: %s' % self.source)
        count = 0
        for row in self.ws.rows:
            count += 1
            if count < 6:
                continue
            self.measurements.append({'slot':       row[1].value,      # sample location
                                      'measure':    self.truefalse(row[2].value),  # filename and visualization
                                      'filename':   row[3].value,
                                      'nscans':     row[4].value,
                                      'start':      row[5].value,
                                      'mode':       row[6].value,
                                      'e0':         row[7].value,      # energy range
                                      'element':    row[8].value,
                                      'edge':       row[9].value,
                                      'focus':      row[10].value,
                                      'sample':     row[11].value,     # scan metadata
                                      'prep':       row[12].value,
                                      'comment':    row[13].value,
                                      'bounds':     row[14].value,     # scan parameters
                                      'steps':      row[15].value,
                                      'times':      row[16].value,
                                      'samplex':    row[17].value,
                                      'sampley':    row[18].value,
                                      'slitwidth':  row[19].value,
                                      'snapshots':  self.truefalse(row[20].value), # flags
                                      'htmlpage':   self.truefalse(row[21].value),
                                      'usbstick':   self.truefalse(row[22].value),
                                      'bothways':   self.truefalse(row[23].value),
                                      'channelcut': self.truefalse(row[24].value),
                                      'ththth':     self.truefalse(row[25].value),
            })
        #pp.pprint(self.measurements)

    def write_macro(self):
        '''Write a macro paragraph for each sample described in the spreadsheet.
        A paragraph consists of line to move to the correct wheel slot, a line
        to change the edge energy (if needed), and a line to measure the XAFS using
        the correct set of control parameters.  Then write out the macro.py file.
        '''
        first_change = not self.do_first_change
        element, edge, focus = (None, None, None)
        self.content = ''
        for m in self.measurements:
            if type(m['slot']) is not int:
                continue
            if type(m['filename']) is None:
                continue
            if  self.truefalse(m['measure']) is False:
                #self.content += self.tab + '## not measuring slot %d\n\n' % m['slot']
                continue
            if m['nscans'] is not None and m['nscans'] < 1:
                #self.content += self.tab + '## zero repetitions of slot %d\n\n' % m['slot']
                continue
            for k in ('element', 'edge'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]
            self.content += self.tab + 'yield from slot(%d)\n' % m['slot']
            if m['samplex'] is not None:
                self.content += self.tab + 'yield from mv(xafs_x, %d)\n' % m['samplex']
            if m['sampley'] is not None:
                self.content += self.tab + 'yield from mv(xafs_y, %d)\n' % m['sampley']
            if m['slitwidth'] is not None:
                self.content += self.tab + 'yield from mv(slits3.hsize, %d)\n' % m['slitwidth']
            
            if m['element'] != element or m['edge'] != edge: # focus...
                element = m['element']
                edge    = m['edge']
                focus   = False
                if m['focus'] == 'focused':
                    focus = True
                if first_change:
                    pass
                    first_change = False
                else:
                    self.content += self.tab + 'yield from change_edge(\'%s\', edge=\'%s\', focus=%r)\n' % (m['element'], m['edge'], focus)
            else:
                #self.content += self.tab + '## staying at %s %s\n' % (m['element'], m['edge'])
                pass

            command = self.tab + 'yield from xafs(\'%s.ini\'' % self.basename
            for k in m.keys():
                ## skip cells with macro-building parameters that are not INI parameters
                if k in ('slot', 'focus', 'measure'):
                    continue
                ## skip the flags for now
                elif k in ('snapshots', 'htmlpage', 'usbstick', 'bothways', 'channelcut', 'ththth'):
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
                    if type(m[k]) is int:
                        command += ', %s=%d' % (k, m[k])
                    elif type(m[k]) is float:
                        command += ', %s=%.3f' % (k, m[k])
                    else:
                        command += ', %s=\'%s\'' % (k, m[k])
            command += ')\n'
            self.content += command
            self.content += self.tab + 'close_last_plot()\n\n'

        #################################
        # write out the master INI file #
        #################################
        config = configparser.ConfigParser()
        default = self.measurements[0].copy()
        for k in ('slot', 'measure', 'focus'): # things in the spreadsheet but not in the INI file
            default.pop(k, None)
        default['experimenters'] = self.ws['E1'].value # top line of xlsx file
        if default['experimenters'] is None or str(default['experimenters']).strip() == '':
            default['experimenters'] = BMMuser.name
        config.read_dict({'scan': default})
        with open(self.ini, 'w') as configfile:
            config.write(configfile)
        print('Default INI file: %s' % self.ini)

        ########################
        # write the full macro #
        ########################
        with open(self.tmpl) as f:
            text = f.readlines()
        o = open(self.macro, 'w')
        o.write(''.join(text).format(folder=self.folder, base=self.basename, content=self.content))
        o.close()
        print('Macro file: %s' % self.macro)

wmb = WheelMacroBuilder()
#wmb.folder = 'foo'
#wmb.do_first_change = True
#wmb.spreadsheet(sys.argv[1])
#wmb.write_macro()
