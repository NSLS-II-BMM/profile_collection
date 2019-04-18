
run_report(__file__)


if BMMuser.pds_mode is None:
    BMMuser.pds_mode = get_mode()

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

        if BMMuser.user_is_defined:
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
    print(bold_msg('Open the shutter:\t\t')+'shb.open()')
    print(bold_msg('Close the shutter:\t\t')+'shb.close()')
    print('')
    print(bold_msg('Change energy:\t\t\t')+'RE(mv(dcm.energy, <energy>))')
    print(bold_msg('Move a motor, absolute:\t\t')+'RE(mv(<motor>, <position>))')
    print(bold_msg('Move a motor, relative:\t\t')+'RE(mvr(<motor>, <delta>))')
    print(bold_msg('Where is a motor?\t\t')+'%w <motor>')
    print('')
    print(bold_msg('Where is the DCM?\t\t')+'%w dcm')
    print(bold_msg('Where is M2?\t\t\t')+'%w m2')
    print(bold_msg('Where is M3?\t\t\t')+'%w m3')
    print(bold_msg('Where are the slits?\t\t')+'%w slits3')
    print(bold_msg('Where is the XAFS table?\t')+'%w xafs_table')
    print('')
    print(bold_msg('Summarize all motor positions:\t')+'%m')
    print(bold_msg('Summarize utilities:\t\t')+'%ut')
    print('')
    print(bold_msg('How long will a scan seq. be?\t')+'howlong(\'scan.ini\')')
    print(bold_msg('Run a scan sequence:\t\t')+'RE(xafs(\'scan.ini\'))')
    print(bold_msg('Scan a motor, plot a detector:\t')+'RE(linescan(<det>, <motor>, <start>, <stop>, <nsteps>))')
    print(bold_msg('Scan 2 motors, plot a detector:\t')+'RE(areascan(<det>, <slow motor>, <start>, <stop>, <nsteps>, <fast motor>, <start>, <stop>, <nsteps>))')
    #print(bold_msg('Single energy XAS detection:\t')+'RE(sead(\'timescan.ini\'))')
    print(bold_msg('Make a log entry:\t\t')+'BMM_log_info(\'blah blah blah\')')
    print('')
    print(bold_msg('DATA = ') + DATA)
    print('')
    print(bold_msg('All the details: ') + url_msg('https://nsls-ii-bmm.github.io/BeamlineManual/index.html'))
    return None

def BMM_keys():
    '''
    Print a concise summary of command line hotkeys.
    '''
    print('')
    print(bold_msg('Abort scan:\t\t')+error_msg('Ctrl-c twice!'))
    print(bold_msg('Search backwards:\t')+'Ctrl-r')
    print(bold_msg('Quit search:\t\t')+'Ctrl-g')
    print(bold_msg('Beginning of line:\t')+'Ctrl-a')
    print(bold_msg('End of line:\t\t')+'Ctrl-e')
    print(bold_msg('Delete character\t')+'Ctrl-d')
    print(bold_msg('Cut text to eol\t\t')+'Ctrl-k')
    print(bold_msg('Cut text to bol\t\t')+'Ctrl-u')
    print(bold_msg('Paste text\t\t')+'Ctrl-y')
    print(bold_msg('Clear screen\t\t')+'Ctrl-l')
    print('')
    print(bold_msg('More details: ') + url_msg('https://jakevdp.github.io/PythonDataScienceHandbook/01.02-shell-keyboard-shortcuts.html'))
    return None


