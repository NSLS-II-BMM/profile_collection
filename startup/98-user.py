import sys
import os

from IPython.terminal.prompts import Prompts, Token
class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        if idps.state.value == 0:
            shatoken = (Token.OutPromptNum, 'A')
        else:
            shatoken = (Token.Tilde, 'A')

        if shb.state.value == 1:
            shbtoken = (Token.OutPromptNum, 'B')
        else:
            shbtoken = (Token.Tilde, 'B')

        return [(Token, '%s.%s ' % (BMM_config._mode, dcm.crystal)),
                (Token.Prompt, '['),
                shatoken,
                (Token.Prompt, '|'),
                shbtoken,
                (Token.Prompt, ']'),
                (Token.Comment, ' %s ' % ring.current.value),
                (Token.Prompt, '['),
                (Token.PromptNum, str(self.shell.execution_count)),
                (Token.Prompt, ']'),
                (Token.Prompt, ' > ')]

ip = get_ipython()
ip.prompts = MyPrompt(ip)

def new_experiment(folder):
    ## make folder
    if not os.path.isdir(folder):
        os.mkdir(folder)
    BMM_user_log(os.path.join(folder, 'experiment.log'))

    startup = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup')

    initmpl = os.path.join(startup, 'scan.tmpl')
    with open(initmpl) as f:
        content = f.readlines()
    scanini = os.path.join(folder, 'scan.ini')
    o = open(scanini, 'w')
    o.write(''.join(content).format(folder=folder))
    o.close()

    macrotmpl = os.path.join(startup, 'macro.tmpl')
    with open(macrotmpl) as f:
        content = f.readlines()
    macropy = os.path.join(folder, 'macro.py')
    o = open(macropy, 'w')
    o.write(''.join(content).format(folder=folder))
    o.close()
