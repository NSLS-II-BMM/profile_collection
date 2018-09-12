import sys
import os

run_report(__file__)

from IPython.terminal.prompts import Prompts, Token
class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        if idps.state.value == 0:
            shatoken = (Token.OutPromptNum, ' A')
        else:
            shatoken = (Token.Tilde, ' A')

        if shb.state.value == 1:
            shbtoken = (Token.OutPromptNum, 'B')
        else:
            shbtoken = (Token.Tilde, 'B')

        ## BMM XRD.311 A•B 0.0 [5] ▶
        return [(Token.CursorLine, 'BMM %s.%s' % (BMM_config._mode, dcm._crystal)),
                shatoken,
                (Token.Prompt, u'\u2022'),
                shbtoken,
                (Token.Comment, ' %.1f ' % ring.current.value),
                (Token.Prompt, '['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, '] ' + u"\u25B6" + ' ')]

ip = get_ipython()
ip.prompts = MyPrompt(ip)


# def explore_tokens(i):
#     tokens = ('Aborted', 'AutoSuggestion', 'ColorColumn', 'Comment',
#               'CursorColumn', 'CursorLine', 'Digraph', 'Error',
#               'Escape', 'Generic', 'Keyword', 'LeadingWhiteSpace',
#               'LineNumber', 'Literal', 'MatchingBracket', 'Menu',
#               'MultipleCursors', 'Name', 'Number', 'Operator',
#               'Other', 'OutPrompt', 'OutPromptNum', 'Prompt',
#               'PromptNum', 'Punctuation', 'Scrollbar', 'SearchMatch',
#               'SelectedText', 'SetCursorPosition', 'String', 'Tab',
#               'Text', 'Tilde', 'Token', 'Toolbar',
#               'TrailingWhiteSpace', 'Transparent', 'WindowTooSmall',
#               'ZeroWidthEscape')
#     class MyPrompt(Prompts):
#         def in_prompt_tokens(self, cli=None):
#             return [(getattr(Token, tokens[i]), 'BMM >'),]
#     ip = get_ipython()
#     ip.prompts = MyPrompt(ip)
#     return 'Token.%s' % tokens[i]

DATA = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'

def new_experiment(folder, gup=0, saf=0):
    '''
    Get ready for a new experiment.  Run this first thing when a user
    sits down to start their beamtime.  This will:
      1. Create a folder, if needed, and set the DATA variable
      2. Set up the experimental log, creating an experiment.log file, if needed
      3. Write templates for scan.ini and macro.py, if needed
      4. Set the 
    '''
    ## make folder
    if not os.path.isdir(folder):
        os.mkdir(folder)
        print('1. Created data folder')
    else:
        print('1. Found data folder')
    imagefolder = os.path.join(folder, 'snapshots')
    if not os.path.isdir(imagefolder):
        os.mkdir(imagefolder)
        print('   Created snapshot folder')
    else:
        print('   Found snapshot folder')
    
    global DATA
    DATA = folder + '/'
    print('   DATA = %s' % DATA)
    print('   snapshots in %s' % imagefolder)

    ## setup logger
    BMM_user_log(os.path.join(folder, 'experiment.log'))
    print('2. Set up experimental log file: %s' % os.path.join(folder, 'experiment.log'))

    startup = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup')

    ## write scan.ini template
    initmpl = os.path.join(startup, 'scan.tmpl')
    scanini = os.path.join(folder, 'scan.ini')
    if not os.path.isfile(scanini):
        with open(initmpl) as f:
            content = f.readlines()
        o = open(scanini, 'w')
        o.write(''.join(content).format(folder=folder))
        o.close()
        print('3. Created INI template: %s' % scanini)
    else:
        print('3. Found INI template: %s' % scanini)

    ## write macro template
    macrotmpl = os.path.join(startup, 'macro.tmpl')
    macropy = os.path.join(folder, 'macro.py')
    if not os.path.isfile(macropy):
        with open(macrotmpl) as f:
            content = f.readlines()
        o = open(macropy, 'w')
        o.write(''.join(content).format(folder=folder))
        o.close()
        print('4. Created macro template: %s' % macropy)
    else:
        print('4. Found macro template: %s' % macropy)

    BMM_xsp.gup = gup
    BMM_xsp.saf = saf
    print('5. Set GUP and SAF numbers as metadata')

    return None
    
def end_experiment():
    '''
    Unset the logger and the DATA variable at the end of an experiment.
    '''
    BMM_unset_user_log()
    global DATA
    DATA = os.path.join(os.environ['HOME'], 'Data', 'bucket') + '/'
    BMM_xsp.gup = 0
    BMM_xsp.saf = 0

    return None

def BMM_help():
    '''
    Print a concise summary of data acquisition commands.
    '''
    print('')
    print(colored('Open the shutter:\t\t', 'white')+'shb.open()')
    print(colored('Close the shutter:\t\t', 'white')+'shb.close()')
    print('')
    print(colored('Change energy:\t\t\t', 'white')+'RE(mv(dcm.energy, <energy>))')
    print(colored('Move a motor, absolute:\t\t', 'white')+'RE(mv(<motor>, <position>))')
    print(colored('Move a motor, relative:\t\t', 'white')+'RE(mvr(<motor>, <delta>))')
    print(colored('Where is a motor?\t\t', 'white')+'<motor>.wh()')
    print('')
    print(colored('Where is the DCM?\t\t', 'white')+'dcm.wh()')
    print(colored('Where is M2?\t\t\t', 'white')+'m2.wh()')
    print(colored('Where is M3?\t\t\t', 'white')+'m3.wh()')
    print(colored('Where are the slits?\t\t', 'white')+'slits3.wh()')
    print(colored('Where is the XAFS table?\t', 'white')+'xafs_table.wh()')
    print('')
    print(colored('Summarize all motor positions:\t', 'white')+'ms()')
    print(colored('Summarize utilities:\t\t', 'white')+'su()')
    print('')
    print(colored('How long will a scan seq. be?\t', 'white')+'howlong(DATA + \'scan.ini\')')
    print(colored('Run a scan sequence:\t\t', 'white')+'RE(xafs(DATA + \'scan.ini\'))')
    print(colored('Scan a motor, plot a detector:\t', 'white')+'RE(linescan(<det>, <motor>, <start>, <stop>, <nsteps>))')
    print(colored('Scan 2 motors, plot a detector:\t', 'white')+'RE(areascan(<det>, <slow motor>, <start>, <stop>, <nsteps>, <fast motor>, <start>, <stop>, <nsteps>))')
    print(colored('Make a log entry:\t\t', 'white')+'BMM_log_info("blah blah blah")')
    print('')
    print(colored('DATA = ', 'white') + DATA)
    print('')
    print(colored('All the details: ', 'white') + colored('https://nsls-ii-bmm.github.io/BeamlineManual/index.html', 'lightblue'))
    return None

def BMM_keys():
    '''
    Print a concise summary of command line hotkeys.
    '''
    print('')
    print(colored('Abort scan:\t\t', 'white')+'Ctrl-c twice!')
    print(colored('Search backwards:\t', 'white')+'Ctrl-r')
    print(colored('Quit search:\t\t', 'white')+'Ctrl-g')
    print(colored('Beginning of line:\t', 'white')+'Ctrl-a')
    print(colored('End of line:\t\t', 'white')+'Ctrl-e')
    print(colored('Delete character\t', 'white')+'Ctrl-d')
    print(colored('Cut text to eol\t\t', 'white')+'Ctrl-k')
    print(colored('Cut text from bol\t', 'white')+'Ctrl-u')
    print(colored('Paste text\t\t', 'white')+'Ctrl-y')
    print('')
    print(colored('More details: ', 'white') + colored('http://readline.kablamo.org/emacs.html', 'lightblue'))
    return None
