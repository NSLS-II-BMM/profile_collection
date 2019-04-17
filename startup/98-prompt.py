
run_report(__file__)


from IPython.terminal.prompts import Prompts, Token
class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        # if idps.state.value == 0:
        #     shatoken = (Token.OutPromptNum, ' A')
        # else:
        #     shatoken = (Token.Tilde, ' A')

        # if shb.state.value == 1:
        #     shbtoken = (Token.OutPromptNum, 'B')
        # else:
        #     shbtoken = (Token.Tilde, 'B')

        if _user_is_defined:
            bmmtoken = (Token.Prompt, 'BMM ')
        else:
            bmmtoken = (Token.OutPrompt, 'BMM ')
        ## BMM XRD.311 A•B 0.0 [5] ▶
        # rcv = None
        # try:
        #     rcv = ring.current.value
        # except:
        #     rcv = None
        # if rcv is None:
        #     rcv = 0
        return [bmmtoken,
                (Token.CursorLine, '%s.%s' % (BMMuser.pds_mode, dcm._crystal)),
                #shatoken,
                #(Token.Prompt, u'\u2022'),
                #shbtoken,
                #(Token.Comment, ' %.1f ' % rcv),
                (Token.Prompt, ' ['),
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
    print(colored('Where is a motor?\t\t', 'white')+'%w <motor>')
    print('')
    print(colored('Where is the DCM?\t\t', 'white')+'%w dcm')
    print(colored('Where is M2?\t\t\t', 'white')+'%w m2')
    print(colored('Where is M3?\t\t\t', 'white')+'%w m3')
    print(colored('Where are the slits?\t\t', 'white')+'%w slits3')
    print(colored('Where is the XAFS table?\t', 'white')+'%w xafs_table')
    print('')
    print(colored('Summarize all motor positions:\t', 'white')+'%m')
    print(colored('Summarize utilities:\t\t', 'white')+'%ut')
    print('')
    print(colored('How long will a scan seq. be?\t', 'white')+'howlong(\'scan.ini\')')
    print(colored('Run a scan sequence:\t\t', 'white')+'RE(xafs(\'scan.ini\'))')
    print(colored('Scan a motor, plot a detector:\t', 'white')+'RE(linescan(<det>, <motor>, <start>, <stop>, <nsteps>))')
    print(colored('Scan 2 motors, plot a detector:\t', 'white')+'RE(areascan(<det>, <slow motor>, <start>, <stop>, <nsteps>, <fast motor>, <start>, <stop>, <nsteps>))')
    #print(colored('Single energy XAS detection:\t', 'white')+'RE(sead(\'timescan.ini\'))')
    print(colored('Make a log entry:\t\t', 'white')+'BMM_log_info(\'blah blah blah\')')
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
    print(colored('Abort scan:\t\t', 'white')+colored('Ctrl-c twice!', 'lightred'))
    print(colored('Search backwards:\t', 'white')+'Ctrl-r')
    print(colored('Quit search:\t\t', 'white')+'Ctrl-g')
    print(colored('Beginning of line:\t', 'white')+'Ctrl-a')
    print(colored('End of line:\t\t', 'white')+'Ctrl-e')
    print(colored('Delete character\t', 'white')+'Ctrl-d')
    print(colored('Cut text to eol\t\t', 'white')+'Ctrl-k')
    print(colored('Cut text to bol\t\t', 'white')+'Ctrl-u')
    print(colored('Paste text\t\t', 'white')+'Ctrl-y')
    print(colored('Clear screen\t\t', 'white')+'Ctrl-l')
    print('')
    print(colored('More details: ', 'white') + colored('https://jakevdp.github.io/PythonDataScienceHandbook/01.02-shell-keyboard-shortcuts.html', 'lightblue'))
    return None


