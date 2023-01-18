
# note that this file will never be imported when using queueserver
# so the explicit calls to IPython functionality should be OK

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


from IPython.terminal.prompts import Prompts, Token
class BMMPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
        # if idps.state.get() == 0:
        #     shatoken = (Token.OutPromptNum, ' A')
        # else:
        #     shatoken = (Token.Tilde, ' A')

        # if shb.state.get() == 1:
        #     shbtoken = (Token.OutPromptNum, 'B')
        # else:
        #     shbtoken = (Token.Tilde, 'B')

        synstoken = (Token.Text, '')
        if BMMuser.syns is True:
            synstoken = (Token.OutPromptNum, '!!! ')
            
        if BMMuser.user_is_defined:
            bmmtoken = (Token.Prompt, 'BMM ')
        else:
            bmmtoken = (Token.OutPrompt, 'BMM ')
        ## BMM XRD.311 A•B 0.0 [5] ▶
        # rcv = None
        # try:
        #     rcv = ring.current.get()
        # except:
        #     rcv = None
        # if rcv is None:
        #     rcv = 0
        return [synstoken,
                bmmtoken,
                (Token.CursorLine, '%s.%s' % (BMMuser.pds_mode, dcm._crystal)),
                #shatoken,
                #(Token.Prompt, u'\u2022'),
                #shbtoken,
                #(Token.Comment, ' %.1f ' % rcv),
                (Token.Prompt, ' ['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, '] ' + u"\u25B6" + ' ')]


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


## from Tom on Gitter: https://gitter.im/NSLS-II/DAMA?at=5cdf02ab7c363c75a7f983e1
import types
get_ipython().display_formatter.formatters['text/plain'].for_type(types.GeneratorType, lambda x, y, z: print(f'{x}   Hint: enclose bsui commands in RE()'))




def BMM_help():
    '''
    Print a concise summary of data acquisition commands.
    '''
    BMMuser = user_ns['BMMuser']
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
    print(bold_msg('DATA = ') + BMMuser.DATA)
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
