
from bluesky.plan_stubs import null, mv

import os, subprocess

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import present_options
from BMM.periodictable import ELEMENTS, Z_number
from BMM.positioning   import find_slot, align_ga
from BMM.xafs          import howlong, xafs

from IPython import get_ipython
user_ns = get_ipython().user_ns

class WDYWTD():
    '''What Do You Want To Do?

    An extremely simple textual user interface to the most commonly
    performed chores at BMM.

    '''
    def wdywtd(self):
        '''Prompt the user to do a thing.
        '''

        actions = {'1':'XAFS', '2':'ChangeEdge', '3':'Spreadsheet', '4':'RunMacro', '5':'AlignSlot', '6':'AlignGA', '7':'XRFSpectrum',
                   'A':'RockingCurve', 'B':'SlitHeight', 'C':'AdjustSlits', 'D':'ChangeXtals', 'E':'SetupXRD',}

        print('''
  COMMON CHORES                            LESS COMMON CHORES
================================================================================
 1. measure XAFS                          A. measure rocking curve
 2. change edge                           B. measure slit height
 3. import spreadsheet                    C. adjust slit size
 4. run macro                             D. change monochrometer crystals
 5. align wheel slot                      E. set up for XRD
 6. align glancing angle stage           
 7. see XRF spectrum

 q. quit
    ''')
        choice = input(" What do you want to do? ")
        choice = choice.upper()
        print('\n')
        def bailout():
            print(whisper('doing nothing'))
            yield from null()
        thing = 'do_nothing'
        if choice in actions:
            thing = f'do_{actions[choice]}'
        return getattr(self, thing, lambda: bailout)()


    def do_nothing(self):
        print(whisper('doing nothing'))
        yield from null()
            
    def do_XAFS(self):
        print(go_msg('You would like to do an XAFS scan...\n'))
        howlong()
        yield from null()
        ##yield from xafs()
            
    def do_ChangeEdge(self):
        print(go_msg('You would like to change to a different edge...\n'))

        el = input(" What element? ")
        el = el.capitalize()
        if el == '':
            print(whisper('doing nothing'))
            return(yield from null())
        if el not in ELEMENTS:
            print(error_msg(f'{el} is not an element'))
            return(yield from null())

        if Z_number(el) < 46:
            default_ed = 'K'
            prompt = go_msg('K') + '/L3/L2/L1'
        else:
            default_ed = 'L3'
            prompt = 'K/' + go_msg('L3') + '/L2/L1'
        ed = input(f' What edge? [{prompt}] ')
        ed = ed.capitalize()
        if ed not in ('K', 'L3', 'L2', 'L1'):
            ed = default_ed

        focus = input(' Focused beam? [y/N] ')
        if focus.lower() == 'y':
            focus = True
        else:
            focus = False

        print(disconnected_msg(f'yield from change_edge("{el}", focus={focus}, edge="{ed}")'))
        yield from null()
        ##yield from change_edge(el, focus=focus, edge=ed)
            
    def do_Spreadsheet(self):
        print(go_msg('You would like to import a spreadsheet...\n'))
        ## prompt for type of spreadsheet: wheel or glancing angle
        user_ns['wmb'].spreadsheet()

        fullpath = os.path.join(user_ns['BMMuser'].folder, user_ns['wmb'].basename+'.py')
        ipython = get_ipython()
        which = input("\n View, run macro, or return? [v/m/r] ")
        if which.startswith('v'):
            #ipython.magic(f'page \'{fullpath}\'')
            subprocess.run([os.environ['PAGER'], f'"{fullpath}"'])
            yield from null()
        elif which.startswith('m'):
            print('run ' + user_ns['wmb'].basename)
            yield from null()
        else:
            yield from null()
            
    def do_RunMacro(self):
        print(go_msg('You would like to run a measurement macro...\n'))
        macro = present_options('py')
        ipython = get_ipython()
        fullpath = os.path.join(user_ns['BMMuser'].folder, macro)
        ipython.magic(f'run -i \'{fullpath}\'')
        print(disconnected_msg(f'yield from {macro[:-3]}()'))
        yield from null()
            
    def do_AlignSlot(self):
        print(go_msg('You would like to align a wheel slot...\n'))
        yield from find_slot()
            
    def do_AlignGA(self):
        print(go_msg('You would like to align the glancing angle stage...\n'))
        yield from align_ga()
            
    def do_RockingCurve(self):
        print(go_msg('You would like to measure a rocking curve scan...\n'))
        print(disconnected_msg('yield from rocking_curve()'))
            
    def do_SlitHeight(self):
        print(go_msg('You would like to set the slit height...\n'))
        print(disconnected_msg('yield from slit_height()'))
            
    def do_AdjustSlits(self):
        print(go_msg('You would like to adjust the size of the hutch slits...\n'))
        which = input(" Horizontal or vertical? [H/v] ")
        which = which.lower()
        if which.startswith('h') or which == '':
            size = input(' Horizontal size (in mm): ')
            is_horiz = True
        elif which.startswith('v'):
            size = input(' Vertical size (in mm): ')
            is_horiz = False
        else:
            self.do_nothing()
            return

        try:
            size = float(size)
        except:
            print(error_msg(f'\n "{size}" cannot be interpreted as a number'))
            yield from null()
            return
        if is_horiz:
            print(disconnected_msg(f'yield from mv(slits3.hsize, {size})'))
            ##yield from mv(slits3.hsize, size)
        else:
            print(disconnected_msg(f'yield from mv(slits3.vsize, {size})'))
            ##yield from mv(slits3.vsize, size)
            
    def do_XRFSpectrum(self):
        print(go_msg('You would like to see an XRF spectrum...\n'))
        user_ns['xs'].measure_xrf()
        yield from null()
            
    def do_ChangeXtals(self):
        if user_ns['dcm']._crystal == '111':
            print(go_msg('You would like to change to the Si(311) crystals...\n'))
            print(disconnected_msg('yield from change_xtals("311")'))
        else:
            print(go_msg('You would like to change to the Si(111) crystals...\n'))
            print(disconnected_msg('yield from change_xtals("111")'))
        yield from null()

    def do_SetupXRD(self):
        print(go_msg('You would like to set up for XRD...\n'))
        print(disconnected_msg('yield from change_edge("Ni", xrd=True, energy=8600)'))
        yield from null()
