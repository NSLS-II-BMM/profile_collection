from BMM.functions import run_report

run_report('\t'+'bsui prompt')

from BMM.prompt import MyPrompt, BMM_help, BMM_keys
ip = get_ipython()
ip.prompts = MyPrompt(ip)

