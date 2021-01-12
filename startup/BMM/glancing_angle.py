
from bluesky.plan_stubs import sleep, mv, mvr, null
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

import os, re
from openpyxl import load_workbook
import configparser
import numpy

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import isfloat, present_options
from BMM.logging        import report
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


class PinWheelMacroBuilder():
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM glancing angle
    stage.

    Examples
    --------
    >>> mb = PinWheelMacroBuilder()
    >>> mb.spreadsheet('wheel1.xlsx')
    >>> mb.write_macro()

    '''
    def __init__(self, folder=None):
        self.basename     = None
        self.folder       = None

        self.source       = None
        self.wb           = None
        self.ws           = None
        self.measurements = list()
        self.ini          = None
        self.macro        = None

        self.tab          = '        '
        self.content      = ''
        self.do_first_change = False
        self.has_e0_column   = False
        self.verbose         = False

        self.instrument   = None

            
    def spreadsheet(self, spreadsheet=None, energy=False):
        '''Convert a wheel macro spreadsheet to a BlueSky plan.

        Examples
        --------
        To create a macro from a spreadsheet called "MySamples.xlsx"

        >>> xlsx('MySamples')

        To specify a change_edge() command at the beginning of the macro:

        >>> xlsx('MySamples', energy=True)

        '''
        if spreadsheet is None:
            spreadsheet = present_options('xlsx')
        if spreadsheet is None:
            print(error_msg('No spreadsheet specified!'))
            return None
        if spreadsheet[-5:] != '.xlsx':
            spreadsheet = spreadsheet+'.xlsx'
        self.source   = os.path.join(self.folder, spreadsheet)
        self.basename = os.path.splitext(spreadsheet)[0]
        self.basename = re.sub('[ -]+', '_', self.basename)
        self.wb       = load_workbook(self.source, read_only=True);
        self.ws       = self.wb.active
        self.ini      = os.path.join(self.folder, self.basename+'.ini')
        self.tmpl     = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup', 'pinwheelmacro.tmpl')
        self.macro    = os.path.join(self.folder, self.basename+'_macro.py')
        self.measurements = list()
        #self.do_first_change = False
        #self.close_shutters  = True
        if energy is True:
            self.do_first_change = True

        self.do_first_change = self.truefalse(self.ws['H2'].value)
        self.close_shutters  = self.truefalse(self.ws['K2'].value)
        self.append_element  = str(self.ws['M2'].value)
        if str(self.ws['B1'].value).lower() == 'glancing angle':
            self.instrument = 'glancing angle'

        if self.instrument != 'glancing angle':
            print(error_msg('This does not appear to be spreadsheet for use with the glancing angle stage.'))
            print(whisper('Cell B1 does not say "Glancing angle".'))
            return None
        
        isok, explanation = self.read_spreadsheet()
        if isok is False:
            print(error_msg(explanation))
            return None
        self.write_macro()
        return 0

        
    def truefalse(self, value):
        '''Interpret certain strings from the spreadsheet as True/False'''
        if value is None:
            return True # self.measurements[0]['measure']
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
        BMMuser = user_ns['BMMuser']
        
        if default['experimenters'] is None or str(default['experimenters']).strip() == '':
            default['experimenters'] = BMMuser.name

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
            
        #if default['mode'] is None or str(default['mode']).strip() == '':
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

        
    def write_macro(self):
        '''Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of line to move to the
        correct wheel slot, a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.  

        Finally, write out the master INI and macro python files.
        '''
        totaltime ,deltatime = 0, 0
        element, edge, focus = (None, None, None)
        self.content = ''
        for m in self.measurements:

            #####################################################
            # all the reasons to skip a line in the spreadsheet #
            #####################################################
            if m['default'] is True:
                element = m['element']
                edge    = m['edge']
                continue
            if type(m['slot']) is not int:
                continue
            if m['filename'] is None or re.search('^\s*$', m['filename']) is not None:
                continue
            if  self.truefalse(m['measure']) is False:
                continue
            if m['nscans'] is not None and m['nscans'] < 1:
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
                totaltime += 4
                
            elif m['element'] != element or m['edge'] != edge: # focus...
                element = m['element']
                edge    = m['edge']
                self.content += self.tab + 'yield from change_edge(\'%s\', edge=\'%s\', focus=%r)\n' % (m['element'], m['edge'], focus)
                totaltime += 4
                
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
                if k in ('default', 'slot', 'spin', 'focus', 'measure', 'method', 'angle'):
                    continue
                ## skip the flags for now
                elif k in ('snapshots', 'htmlpage', 'usbstick', 'bothways', 'channelcut', 'ththth'):
                    continue
                ## motor alignment cells
                elif k in ('samplep', 'sampley'):
                    continue
                ## placeholders for scientific metadata
                elif k in ('url', 'doi', 'cif'):
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
                        fname = m[k]
                        el = self.measurements[0]['element']
                        ed = self.measurements[0]['edge']
                        if 'element' in m:
                            el = m['element']
                        if 'edge' in m:
                            ed = m['edge']
                        if self.append_element.lower() == 'element at beginning':
                            fname = el + '-' + fname
                        elif self.append_element.lower() == 'element at end':
                            fname = fname + '-' + el
                        elif self.append_element.lower() == 'element+edge at beginning':
                            fname = el + '-' + ed + '-' +  fname
                        elif self.append_element.lower() == 'element+edge at end':
                            fname = fname + '-' + el + '-' + ed
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
                
            (e,t,at,delta) = conventional_grid(bounds=b, steps=s, times=t, e0=edge_energy(element, edge), element=element, edge=edge, ththth=False)
            
            if type(m['nscans']) is int:
                nsc = m['nscans']
            else:
                nsc = self.measurements[0]['nscans']
            totaltime += at * nsc
            deltatime += delta*delta
            

        if self.close_shutters:
            self.content += self.tab + 'if not dryrun:\n'
            self.content += self.tab + '    yield from shb.close_plan()\n'

            
        #################################
        # write out the master INI file #
        #################################
        config = configparser.ConfigParser()
        default = self.measurements[0].copy()
        for k in ('default', 'slot', 'measure', 'spin', 'focus', 'method', 'samplep', 'sampley', 'slitwidth'): # things in the spreadsheet but not in the INI file
            default.pop(k, None)
        default['url'] = '...'
        default['doi'] = '...'
        default['cif'] = '...'
        default['experimenters'] = self.ws['E1'].value # top line of xlsx file
        default = self.ini_sanity(default)
        if default is None:
            print(error_msg("Could not interpret %s as a wheel macro." % self.source))
            return
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
        from IPython import get_ipython
        ipython = get_ipython()
        ipython.magic('run -i \'%s\'' % self.macro)
        print(whisper('Wrote and read macro file: %s' % self.macro))

        #######################################
        # explain to the user what to do next #
        #######################################
        print('\nYour new glancing angle plan is called: ' + bold_msg('%s_macro' % self.basename))
        print('\nVerify: ' + bold_msg('%s_macro??' % self.basename))
        print('Dryrun: '   + bold_msg('RE(%s_macro(dryrun=True))' % self.basename))
        print('Run:    '   + bold_msg('RE(%s_macro())' % self.basename))
        hours = int(totaltime/60)
        minutes = int(totaltime - hours*60)
        deltatime = numpy.sqrt(deltatime)
        print(f'\nApproximate time: {hours} hours, {minutes} minutes +/- {deltatime:.1f} minutes')

            
    def read_spreadsheet(self):
        '''Slurp up the content of the spreadsheet and write the default control file
        '''
        print('Reading spreadsheet: %s' % self.source)
        count = 0
        isok, explanation = True, ''
        if self.has_e0_column:  # deal with older xlsx that have e0 in column H
            offset = 1

        for row in self.ws.rows:
            count += 1
            if count < 6:
                continue
            defaultline = False
            if count == 6:
                defaultline = True
            if count > 200:
                break
            self.measurements.append({'default' :   defaultline,
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
                                      'cif':        row[28].value,
            })
            
            ## check that scan parameters make sense
            if type(self.measurements[-1]['bounds']) is str:
                b = re.split('[ ,]+', self.measurements[-1]['bounds'])
            else:
                b = re.split('[ ,]+', self.measurements[0]['bounds'])
            if type(self.measurements[-1]['steps']) is str:
                s = re.split('[ ,]+', self.measurements[-1]['steps'])
            else:
                s = re.split('[ ,]+', self.measurements[0]['steps'])
            if type(self.measurements[-1]['times']) is str:
                t = re.split('[ ,]+', self.measurements[-1]['times'])
            else:
                t = re.split('[ ,]+', self.measurements[0]['times'])

            (problem, text ) = sanitize_step_scan_parameters(b, s, t)
            if problem is True:
                isok = False
                explanation += f'row {count}:\n' + text
        return(isok, explanation)
        #pp.pprint(self.measurements)
        
