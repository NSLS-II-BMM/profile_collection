import sys
import os

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

        return [(Token.CursorLine, 'BMM '),
                (Token.CursorLine, '%s.%s' % (BMM_config._mode, dcm.crystal)),
                shatoken,
                (Token.Prompt, u'\u2022'),
                shbtoken,
                (Token.Comment, ' %.1f ' % ring.current.value),
                (Token.Prompt, '['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, '] ' + u"\u25B6"+' ')]

ip = get_ipython()
ip.prompts = MyPrompt(ip)

def new_experiment(folder):
    ## make folder
    if not os.path.isdir(folder):
        os.mkdir(folder)
        print('1. Created data folder: %s' % folder)
    else:
        print('1. Found data folder: %s' % folder)

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
