
import os, re, numpy, configparser
from openpyxl import load_workbook


from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import isfloat, present_options
from BMM.gdrive         import copy_to_gdrive
from BMM.periodictable  import PERIODIC_TABLE, edge_energy
from BMM.xafs_functions import conventional_grid, sanitize_step_scan_parameters

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.bmm import BMMuser

class BMMMacroBuilder():
    '''A base class for parsing specially constructed spreadsheets and
    generating the corresponding BlueSky plan.

    attributes
    ----------
    basename : str
       basename of the spreadsheet or name of the sheet
    folder : str
       folder containing spreadsheet, usually same as BMMuser.folder
    joiner : str
       string used to construct filenames [-] (_ is a also a good choice)
    source : str
       fully resolved path to spreadsheet
    wb : openpyxl workbook object
       workbook created from spreadsheet
    ws : openpyxl worksheet object
       main sheet of spreadsheet
    measurements : list
       list of disctionaries, one for each row of the spreadsheet
    ini : str
       fully resolved path to INI file
    macro : str
       fully resolved path to plan file
    tab : str
       string used to pythonically format the plan file
    content : str
       accumulated content of plan
    do_first_change : bool
       True is need to begin with a change_edge()
    has_e0_column : bool
       True is this is a very old wheel spreadsheet
    offset : int
       1 if this is a very old wheel spreadsheet
    verbose : bool
       True for more comment lines in  the plan 
    totaltime : float
       estimate for the run time of the plan
    deltatime : float
       estimated uncertainty in the total time estimate
    instrument : str
       "sample wheel" or "glancing angle stage"

    Required method
    ---------------
    _write_macro
       generate the text of the BlueSky plan
    get_keywords
       instructions for parsing spreadsheet columns into keywords
    
    '''
    def __init__(self, folder=None):
        self.basename         = None
        self.folder           = None
        self.joiner           = '-'

        self.source           = None
        self.wb               = None
        self.ws               = None
        self.measurements     = list()
        self.ini              = None
        self.macro            = None

        self.tab              = ' ' * 8
        self.content          = ''
        self.do_first_change  = False
        self.has_e0_column    = False
        self.offset           = 0
        self.verbose          = False

        self.double           = False
        self.inner_position   = 130.324
        self.outer_position   = 104.324
        
        self.totaltime        = 0
        self.deltatime        = 0

        self.tmpl             = None
        self.instrument       = None

        self.experiment       = ('default', 'slot', 'ring', 'temperature', 'focus', 'measure', 'spin', 'angle', 'method')
        self.flags            = ('snapshots', 'htmlpage', 'usbstick', 'bothways', 'channelcut', 'ththth')
        self.motors           = ('samplex', 'sampley', 'samplep', 'slitwidth', 'detectorx')
        self.science_metadata = ('url', 'doi', 'cif')
        
    def spreadsheet(self, spreadsheet=None, sheet=None, double=False):
        '''Convert an experiment description spreadsheet to a BlueSky plan.

        Usually called with no arguments, in which case the user will
        be prompted in the bsui shell for a .xlsx file in the data
        directory.  If the .xlsx file has more that one sheet, the
        user will also be prompted for the sheet name.

        Arguments
        =========
        spreadsheet : str
           The fully resolved path to the .xlsx file
        sheet : int/str/None
           The sheet to read from the spreadsheet file. If int, 
           interpret as the index of the sheetnames list, if str 
           interpret as the name from the sheetnames list, if None 
           use the active sheet as determined by openpyxl.

        '''
        if spreadsheet is None:
            spreadsheet = present_options('xlsx')
        if spreadsheet is None:
            print(error_msg('No spreadsheet specified!'))
            return None
        if spreadsheet[-5:] != '.xlsx':
            spreadsheet = spreadsheet+'.xlsx'
        self.folder   = BMMuser.folder
        self.source   = os.path.join(self.folder, spreadsheet)
        self.basename = os.path.splitext(spreadsheet)[0]
        self.wb       = load_workbook(self.source, read_only=True);
        self.measurements = list()
        # self.do_first_change = False
        # self.close_shutters  = True

        self.double = double

        #print(f'-----{sheet}')
        if sheet is None:
            self.ws = self.wb.active
        elif type(sheet) is int:
            this = self.wb.sheetnames[sheet-1]
            self.ws = self.wb[this]
            self.basename = this
        elif sheet in self.wb.sheetnames:
            self.ws = self.wb[sheet]
            self.basename = sheet
        else:
            self.ws = self.wb.active
        self.basename = re.sub('[ -]+', '_', self.basename)
        self.ini      = os.path.join(self.folder, self.basename+'.ini')
        self.macro    = os.path.join(self.folder, self.basename+'_macro.py')

        if self.ws['H5'].value.lower() == 'e0':  # accommodate older xlsx files which have e0 values in column H
            self.has_e0_column = True

        if double is True:
            self.do_first_change = self.truefalse(self.ws['H2'].value)
            self.close_shutters  = self.truefalse(self.ws['K2'].value)
            self.append_element  = str(self.ws['M2'].value)
        else:
            self.do_first_change = self.truefalse(self.ws['G2'].value)
            self.close_shutters  = self.truefalse(self.ws['J2'].value)
            self.append_element  = str(self.ws['L2'].value)

        self.instrument = str(self.ws['B1'].value).lower()
        self.version = str(self.ws['B2'].value).lower()

        isok, explanation = self.read_spreadsheet()
        if isok is False:
            print(error_msg(explanation))
            return None
        self.write_macro()
        copy_to_gdrive(spreadsheet)
        return 0

    def truefalse(self, value):
        '''Interpret certain strings from the spreadsheet as True/False'''
        if value is None:
            return True  # self.measurements[0]['measure']
        if str(value).lower() == '=true()':
            return True
        elif str(value).lower() == 'true':
            return True
        elif str(value).lower() == 'yes':
            return True
        else:
            return False

    def ini_sanity(self, default):
        '''Sanity checks for the default line from the spreadsheet.

        1. experimenters is a string (BMMuser.name)
        2. sample, prep, and comment are not empty strings (set to '...')
        3. nscans is an integer (set to 1)
        4. start is an integer or "next"
        5. mode is string (set to 'transmission')
        6. element is an element (bail)
        7. edge is k, l1, l2, or l3 (bail)

        To do:
          * booleans are interpretable as booleans
          * focused is focused or unfocused
          * bounds, steps, times are sensible
          * x, y, slits are floats and sensible for the respective ranges of motion

        '''

        message = ''
        unrecoverable = False

        if 'mode' not in default:
            if 'glancing angle' in self.instrument:
                default['mode'] = 'xs'
            else:
                default['mode'] = 'transmission'

        if default['filename'] is None or str(default['filename']).strip() == '':
            default['filename'] = 'filename'

        if default['experimenters'] is None or str(default['experimenters']).strip() == '':
            default['experimenters'] = BMMuser.name

        defaultdefaults = {'bounds': '-200  -30  -10 15.5  570', 'steps': '10  2  0.25  0.05k', 'times': '1 1 1 1'}
        for k in ('bounds', 'steps', 'times'):
            if default[k] is None or str(default[k]).strip() == '':
                default[k] = defaultdefaults[k]

        for k in ('sample', 'prep', 'comment'):
            if default[k] is None or str(default[k]).strip() == '':
                default[k] = '...'
            if '%' in default[k]:
                default[k] = default[k].replace('%', '%%')

        try:
            default['nscans'] = int(default['nscans'])
        except:
            default['nscans'] = 1

        try:
            default['start'] = int(default['start'])
        except:
            default['start'] = 'next'

        # if default['mode'] is None or str(default['mode']).strip() == '':
        #    default['mode'] = 'transmission'

        if str(default['element']).capitalize() not in re.split('\s+', PERIODIC_TABLE): # see 06-periodic table 
            message += '\nDefault entry for element is not recognized.'
            unrecoverable = True

        if str(default['edge']).lower() not in ('k', 'l1', 'l2', 'l3'):
            message += '\nDefault entry for edge is not recognized.'
            unrecoverable = True

        # try:
        #     default['e0'] = float(default['e0'])
        # except:
        #     default['e0'] = edge_energy(default['element'], default['edge'])

        if unrecoverable:
            print(error_msg(message))
            default = None
        return default

    def read_spreadsheet(self):
        '''Slurp up the content of the spreadsheet and write the default control file
        '''
        print('Reading spreadsheet: %s' % self.source)
        count = 0
        self.offset = 0
        isok, explanation = True, ''
        if self.has_e0_column:  # deal with older xlsx that have e0 in column H
            self.offset = 1

        for row in self.ws.rows:
            count += 1
            if count < 6:
                continue
            defaultline = False
            if count == 6:
                defaultline = True
            if count > 200:
                break
            self.measurements.append(self.get_keywords(row, defaultline))

            # check that scan parameters make sense
            if type(self.measurements[-1]['bounds']) is str:
                b = re.split('[ ,]+', self.measurements[-1]['bounds'].strip())
            else:
                b = re.split('[ ,]+', self.measurements[0]['bounds'].strip())
            if type(self.measurements[-1]['steps']) is str:
                s = re.split('[ ,]+', self.measurements[-1]['steps'].strip())
            else:
                s = re.split('[ ,]+', self.measurements[0]['steps'].strip())
            if type(self.measurements[-1]['times']) is str:
                t = re.split('[ ,]+', self.measurements[-1]['times'].strip())
            else:
                t = re.split('[ ,]+', self.measurements[0]['times'].strip())

            (problem, text) = sanitize_step_scan_parameters(b, s, t)
            if problem is True:
                isok = False
                explanation += f'row {count}:\n' + text
        return(isok, explanation)
        # pp.pprint(self.measurements)


    def skip_row(self, m):
        #####################################################
        # all the reasons to skip a line in the spreadsheet #
        #####################################################
        if 'slot' in m and type(m['slot']) is not int:
            return True
        if 'temperature' in m and type(m['temperature']) is not float:
            return True
        if m['filename'] is None or re.search('^\s*$', m['filename']) is not None:
            return True
        if  self.truefalse(m['measure']) is False:
            return True
        if m['nscans'] is not None and m['nscans'] < 1:
            return True
        return False

    def skip_keyword(self, k):
        '''Identify all the keywords that should NOT be captured in the xafs() call.'''
        if k in self.experiment or k in self.flags or k in self.motors or k in self.science_metadata:
            return True
        return False

    def make_filename(self, m):
        '''Construct a filename with element and edge symbols, if required.'''
        fname = m['filename']
        el = self.measurements[0]['element']
        ed = self.measurements[0]['edge']
        t = ''
        if 'temperature' in self.measurements[0]:
            t  = str(self.measurements[0]['temperature'])
        if 'element' in m:
            el = m['element']
        if 'edge' in m:
            ed = m['edge']
        if 'temperature' in m:
            t = str(m['temperature'])
        if self.append_element.lower() == 'element at beginning':
            fname = el + self.joiner + fname
        elif self.append_element.lower() == 'element at end':
            fname = fname + self.joiner + el
        elif self.append_element.lower() == 'element+edge at beginning':
            fname = el + self.joiner + ed + self.joiner + fname
        elif self.append_element.lower() == 'element+edge at end':
            fname = fname + self.joiner + el + self.joiner + ed
        elif self.append_element.lower() == 'temperature at beginning':
            fname = t + self.joiner + fname
        elif self.append_element.lower() == 'temperature at end':
            fname = fname + self.joiner + t
        elif self.append_element.lower() == 'temperature+element at beginning':
            fname = el + self.joiner + t + self.joiner + fname
        elif self.append_element.lower() == 'temperature+element at end':
            fname = fname + self.joiner + el + self.joiner + t
        elif self.append_element.lower() == 'temperature+element+edge at beginning':
            fname = el + self.joiner + ed + self.joiner + t + self.joiner + fname
        elif self.append_element.lower() == 'temperature+element+edge at end':
            fname = fname + self.joiner + el + self.joiner + ed + self.joiner + t
            
        return fname

    def estimate_time(self, m, el, ed):
        '''Approximate the time contribution from the current row'''
        if type(m['bounds']) is str:
            b = re.split('[ ,]+', m['bounds'].strip())
        else:
            b = re.split('[ ,]+', self.measurements[0]['bounds'].strip())
        if type(m['steps']) is str:
            s = re.split('[ ,]+', m['steps'].strip())
        else:
            s = re.split('[ ,]+', self.measurements[0]['steps'].strip())
        if type(m['times']) is str:
            t = re.split('[ ,]+', m['times'].strip())
        else:
            t = re.split('[ ,]+', self.measurements[0]['times'].strip())

        b = [float(x) if isfloat(x) else x for x in b]
        s = [float(x) if isfloat(x) else x for x in s]
        t = [float(x) if isfloat(x) else x for x in t]

        (e, t, at, delta) = conventional_grid(bounds=b, steps=s, times=t, e0=edge_energy(el, ed), element=el, edge=ed, ththth=False)

        if type(m['nscans']) is int:
            nsc = m['nscans']
        else:
            nsc = self.measurements[0]['nscans']
        self.totaltime += at * nsc
        self.deltatime += delta*delta

    def write_ini_and_plan(self):
        #################################
        # write out the master INI file #
        #################################
        config = configparser.ConfigParser()
        default = self.measurements[0].copy()
        #          things in the spreadsheet but not in the INI file
        for k in ('default', 'slot', 'measure', 'spin', 'focus', 'method', 'samplep', 'samplex', 'sampley', 'slitwidth', 'detectorx'):
            default.pop(k, None)
        default['url'] = '...'
        default['doi'] = '...'
        default['cif'] = '...'
        default['experimenters'] = self.ws['E1'].value  # top line of xlsx file
        default = self.ini_sanity(default)
        if default is None:
            print(error_msg(f'Could not interpret {self.source} as a wheel macro.'))
            return
        # print(default)
        config.read_dict({'scan': default})
        with open(self.ini, 'w') as configfile:
            config.write(configfile)
        print(whisper('Wrote default INI file: %s' % self.ini))

        ########################################################
        # write the full macro to a file and %run -i that file #
        ########################################################
        with open(self.tmpl) as f:
            text = f.readlines()
        fullmacro = ''.join(text).format(folder=self.folder, base=self.basename, content=self.content)
        o = open(self.macro, 'w')
        o.write(fullmacro)
        o.close()
        ## I think this will never be called by queueserver
        from IPython import get_ipython
        ipython = get_ipython()
        ipython.magic('run -i \'%s\'' % self.macro)
        print(whisper('Wrote and read macro file: %s' % self.macro))

    def finish_macro(self):
        #######################################
        # explain to the user what to do next #
        #######################################
        print('\nYour new glancing angle plan is called: ' + bold_msg('%s_macro' % self.basename))
        print('\nVerify:  ' + bold_msg('%s_macro??' % self.basename))
        if 'glancing angle' in self.instrument:
            print('Run:     '   + bold_msg('RE(%s_macro())' % self.basename))
            print('Add ref: '   + bold_msg('RE(%s_macro(ref=True))' % self.basename))
        else:
            print('Run:     '   + bold_msg('RE(%s_macro())' % self.basename))
            #print('Dryrun:  '   + bold_msg('RE(%s_macro(dryrun=True))' % self.basename))
        hours = int(self.totaltime/60)
        minutes = int(self.totaltime - hours*60)
        self.deltatime = numpy.sqrt(self.deltatime)
        print(f'\nApproximate time: {hours} hours, {minutes} minutes +/- {self.deltatime:.1f} minutes')

    def write_macro(self):
        '''Write INI file and a BlueSky plan from a spreadsheet.

        Call the subclass' _write_macro to generate the text of the plan.

        '''
        self.totaltime, self.deltatime = 0, 0
        self.content = ''
        self._write_macro()     # populate self.content
        # write_ini_and_plan uses self.measurements and self.content
        self.write_ini_and_plan()
        self.finish_macro()
