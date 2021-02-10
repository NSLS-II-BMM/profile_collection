
from bluesky.plan_stubs import sleep, mv, mvr, null
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

import os, re
from openpyxl import load_workbook
import configparser
import numpy

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from lmfit.models import StepModel
from scipy.ndimage import center_of_mass

from BMM.derivedplot    import close_all_plots, close_last_plot
from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions      import isfloat, present_options, now
from BMM.logging        import report, img_to_slack, post_to_slack
from BMM.linescans      import linescan
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
    inverted = ''
    flat = [0,0]
    y_uid = ''
    pitch_uid = ''
    f_uid = ''
    alignment_filename = ''
    
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


    def pitch_plot(self, pitch, signal, filename=None):
        target = signal.idxmax()
        plt.cla()
        plt.plot(pitch, signal)
        plt.scatter(pitch[target], signal.max(), s=160, marker='x', color='green')
        plt.xlabel('xafs_pitch (deg)')
        plt.ylabel('It/I0')
        plt.title(f'pitch scan, spinner {self.current()}')
        plt.show()
        plt.pause(0.05)
        
            
    def align_pitch(self, force=False):
        xafs_pitch = user_ns['xafs_pitch']
        db = user_ns['db']
        yield from linescan(xafs_pitch, 'it', -2.5, 2.5, 51, pluck=False, force=force)
        close_last_plot()
        table  = db[-1].table()
        pitch  = table['xafs_pitch']
        signal = table['It']/table['I0']
        target = signal.idxmax()
        self.pitch_plot(pitch, signal)
        yield from mv(xafs_pitch, pitch[target])
    

    def y_plot(self, yy, out, filename=None):
        plt.cla()
        plt.scatter(yy, out.data)
        plt.plot(yy, out.best_fit, color='red')
        plt.scatter(out.params['center'].value, out.params['amplitude'].value/2, s=160, marker='x', color='green')
        plt.xlabel('xafs_y (mm)')
        plt.ylabel(f'{self.inverted}data and error function')
        plt.title(f'fit to Y scan, spinner {self.current()}')
        plt.show()
        plt.pause(0.05)


    def alignment_plot(self, yt, pitch, yf):
        db, BMMuser = user_ns['db'], user_ns['BMMuser']
        fig = plt.figure(tight_layout=True) #, figsize=(9,6))
        gs = gridspec.GridSpec(1,3)


        t  = fig.add_subplot(gs[0, 0])
        tt = db[yt].table()
        yy = tt['xafs_y']
        signal = tt['It']/tt['I0']
        if float(signal[2]) > list(signal)[-2] :
            ss     = -(signal - signal[2])
            self.inverted = 'inverted '
        else:
            ss     = signal - signal[2]
            self.inverted    = ''
        mod    = StepModel(form='erf')
        pars   = mod.guess(ss, x=numpy.array(yy))
        out    = mod.fit(ss, pars, x=numpy.array(yy))
        t.scatter(yy, out.data)
        t.plot(yy, out.best_fit, color='red')
        t.scatter(out.params['center'].value, out.params['amplitude'].value/2, s=120, marker='x', color='green')
        t.set_xlabel('xafs_y (mm)')
        t.set_ylabel(f'{self.inverted}data and error function')

        p  = fig.add_subplot(gs[0, 1])
        tp = db[pitch].table()
        xp = tp['xafs_pitch']
        signal = tp['It']/tp['I0']
        target = signal.idxmax()
        p.plot(xp, signal)
        p.scatter(xp[target], signal.max(), s=120, marker='x', color='green')
        p.set_xlabel('xafs_pitch (deg)')
        p.set_ylabel('It/I0')
        p.set_title(f'alignment of spinner {self.current()}')

        f = fig.add_subplot(gs[0, 2])
        tf = db[yf].table()
        yy = tf['xafs_y']
        signal = (tf[BMMuser.xs1] + tf[BMMuser.xs2] + tf[BMMuser.xs3] + tf[BMMuser.xs4]) / tf['I0']
        com = int(center_of_mass(signal)[0])+1
        centroid = yy[com]
        f.plot(yy, signal)
        f.scatter(centroid, signal[com], s=120, marker='x', color='green')
        f.set_xlabel('xafs_y (mm)')
        f.set_ylabel('If/I0')
        
        plt.pause(0.05)

        
    def align_y(self, force=False):
        xafs_y = user_ns['xafs_y']
        db = user_ns['db']
        yield from linescan(xafs_y, 'it', -1, 1, 31, pluck=False)
        close_last_plot()
        table  = db[-1].table()
        yy     = table['xafs_y']
        signal = table['It']/table['I0']
        if float(signal[2]) > list(signal)[-2] :
            ss     = -(signal - signal[2])
            self.inverted = 'inverted '
        else:
            ss     = signal - signal[2]
            self.inverted    = ''
        mod    = StepModel(form='erf')
        pars   = mod.guess(ss, x=numpy.array(yy))
        out    = mod.fit(ss, pars, x=numpy.array(yy))
        print(whisper(out.fit_report(min_correl=0)))
        self.y_plot(yy, out)
        target = out.params['center'].value
        yield from mv(xafs_y, target)


    def auto_align(self, pitch=2):
        BMMuser, db, xafs_pitch, xafs_y = user_ns['BMMuser'], user_ns['db'], user_ns['xafs_pitch'], user_ns['xafs_y']
        report(f'Auto-aligning glancing angle stage, spinner {self.current()}', level='bold', slack=True)

        ## first pass in transmission
        yield from self.align_y()
        yield from self.align_pitch()

        ## for realsies Y in transmission
        yield from self.align_y()
        self.y_uid = db.v2[-1].metadata['start']['uid'] 

        ## for realsies Y in pitch
        yield from self.align_pitch()
        self.pitch_uid = db.v2[-1].metadata['start']['uid'] 

        ## record the flat position
        self.flat = [xafs_y.position, xafs_pitch.position]

        ## move to measurement angle and align
        yield from mvr(xafs_pitch, pitch)
        yield from linescan(xafs_y, 'xs', -2, 1.7, 31, pluck=False)
        self.f_uid = db.v2[-1].metadata['start']['uid'] 
        tf = db[-1].table()
        yy = tf['xafs_y']
        signal = (tf[BMMuser.xs1] + tf[BMMuser.xs2] + tf[BMMuser.xs3] + tf[BMMuser.xs4]) / tf['I0']
        com = int(center_of_mass(signal)[0])+1
        centroid = yy[com]
        yield from mv(xafs_y, centroid)
        
        ## make a pretty picture, post it to slack
        self.alignment_plot(self.y_uid, self.pitch_uid, self.f_uid)
        self.alignment_filename = os.path.join(BMMuser.folder, 'snapshots', f'spinner{self.current()}-alignment-{now()}.png')
        plt.savefig(self.alignment_filename)
        try:
            img_to_slack(self.alignment_filename)
        except:
            post_to_slack('failed to post image: {self.alignment_filename}')
            pass

        
    def flatten(self):
        xafs_pitch, xafs_y = user_ns['xafs_pitch'], user_ns['xafs_y']
        if self.flat != [0, 0]:
            yield from mv(xafs_y, self.flat[0], xafs_pitch, self.flat[1])
        

            

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
            if m['method'].lower() == 'automatic':
                self.content += self.tab + 'yield from mvr(xafs_lins, 5)\n'
            self.content += self.tab + f'yield from ga.to({m["slot"]})\n'
            if m['method'].lower() == 'automatic':
                self.content += self.tab + f'yield from ga.auto_align(pitch={m["angle"]})\n'
                self.content += self.tab + 'yield from mvr(xafs_lins, -5)\n'
            else:
                if m['sampley'] is not None:
                    self.content += self.tab + f'yield from mv(xafs_y, {m["sampley"]})\n'
                if m['samplep'] is not None:
                    self.content += self.tab + f'yield from mv(xafs_pitch, {m["samplep"]})\n'
                #self.content += self.tab + f'ga.flat = [{xafs_y.position}, {xafs_pitch.position}]\n'
                #self.content += self.tab + f'yield from mvr(xafs_pitch, {m["angle"]})\n'

                    
            ############################################################
            # measure XAFS, then return to 0 pitch and close all plots #
            ############################################################
            #self.content += self.tab + 'yield from mvr(xafs_y, -5)\n'
            #self.content += self.tab + f'yield from xafs("{self.basename}.ini", mode="reference", filename="Nbfoil", nscans=1, sample="Nb foil", bounds="-40 40", steps="0.5", times="0.5")\n'
            #self.content += self.tab + 'yield from mvr(xafs_y, 5)\n'
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
            if m['method'].lower() == 'automatic':
                self.content += self.tab + 'yield from mvr(xafs_lins, 5)\n'
                self.content += self.tab + 'yield from ga.flatten()\n'
                self.content += self.tab + 'yield from mvr(xafs_lins, -5)\n'
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

