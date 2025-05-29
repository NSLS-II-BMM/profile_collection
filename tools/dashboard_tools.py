import sys, json, datetime
from termcolor import colored

import redis
redis_host = 'xf06bm-ioc2'
rkvs = redis.Redis(host=redis_host, port=6379, db=0)

HBARC = 1973.27053324
strut = u'\u25CF'
triangle = u'\u227b' # 5BA'




#heartbeat = '⣷⣯⣟⡿⢿⣻⣽⣾' # '<^>v'  # '.o0o' # '-\|/'
heartbeat = '-\|/'
# heartbeat = ['|.    |',
#              '| o   |',
#              '|  0  |', 
#              '|   o |', 
#              '|    .|', 
#              '|   o |', 
#              '|  0  |', 
#              '| o   |',
#              ]
# heartbeat = ['|▁            |',
#              '|  ▃          |',
#              '|    ▅        |',
#              '|      ▇      |',
#              '|        ▆    |',
#              '|          ▄  |',
#              '|            ▁|',
#              '|          ▄  |',
#              '|        ▆    |',
#              '|      ▇      |',
#              '|    ▅        |',
#              '|  ▃          |',
#              ]


def writeline(string):
    #sys.stdout.write('\r')
    #sys.stdout.flush()
    #os.system('clear')
    print('\n\n')
    sys.stdout.write(string)
    sys.stdout.flush()


def rack_string(racks):
    trigger = 24
    string = ''
    color = 'red' if racks[0].get() > trigger else 'green'
    string += colored('A', color, attrs=['bold'])
    color = 'red' if racks[1].get() > trigger else 'green'
    string += colored('B', color, attrs=['bold'])
    color = 'red' if racks[2].get() > trigger else 'green'
    string += colored('1', color, attrs=['bold'])
    color = 'red' if racks[3].get() > trigger else 'green'
    string += colored('2', color, attrs=['bold'])
    color = 'red' if racks[4].get() > trigger else 'green'
    string += colored('3', color, attrs=['bold'])
    return string


def vac_string(vac):
    string = ''
    for count, pv in enumerate(vac):
        if pv.connected is False:
            color = 'blue'
        elif pv.get() == 'LO<E-11':
            color = 'blue'
        elif pv.get() in ('OFF', 'WAIT', 'PROT_OFF'):
            color = 'blue'
        elif float(pv.get()) > 5.0e-7:
            color = 'red'
        elif float(pv.get()) > 9.0e-8:
            color = 'yellow'
        else:
            color =  'green'
        string += colored('%d' % (count+1), color, attrs=['bold'])
    return string

def temperature_string(temperatures):
    def talarm_state(index):
        if index < 2:
            return float(temperatures[index].get()) > float(temperatures[index].upper_warning_limit)
        else:
            return float(temperatures[index].get()) > 0.62*float(temperatures[index].upper_warning_limit)

    string = '('
    color = 'red' if talarm_state(0) else 'green'
    string += colored('111 ', color, attrs=['bold'])
    color = 'red' if talarm_state(1) else 'green'
    string += colored('311 ', color, attrs=['bold'])
    color = 'red' if talarm_state(2) else 'green'
    string += colored('Co ',  color, attrs=['bold'])
    color = 'red' if talarm_state(3) else 'green'
    string += colored('P2 ',  color, attrs=['bold'])
    color = 'red' if talarm_state(4) else 'green'
    string += colored('R2 ',  color, attrs=['bold'])
    color = 'red' if talarm_state(5) else 'green'
    string += colored('Pe ',  color, attrs=['bold'])
    color = 'red' if talarm_state(6) else 'green'
    string += colored('Pa',   color, attrs=['bold'])
    string += ') ('
    color = 'red' if talarm_state(7) else 'green'
    string += colored('U2 ',  color, attrs=['bold'])
    color = 'red' if talarm_state(8) else 'green'
    string += colored('D2',   color, attrs=['bold'])
    string += ') ('
    color = 'red' if talarm_state(9) else 'green'
    string += colored('U3 ',  color, attrs=['bold'])
    color = 'red' if talarm_state(10) else 'green'
    string += colored('D3',   color, attrs=['bold']) + ')'
    return string


def valves_string(fe_valves, valves, maintenance):
    string = 'FE:'
    #if maintenance is False:
    #    string += colored('123', 'red', attrs=['bold'])
    try:
        for count, pv in enumerate(fe_valves):
            color = 'green' if fe_valves[count].get() == 1 else 'red'
            string += colored('%d' % (count+1), color, attrs=['bold'])
    except:
        string += colored('123', 'red', attrs=['bold'])
    string += ' BL:'
    for count, pv in enumerate(valves):
        color = 'green' if valves[count].get() == 1 else 'red'
        string += colored('%d' % (count+1), color, attrs=['bold'])
    return string

def ln2_string(ln2):
    if ln2.get() == 1:
        return colored('LN', 'blue', attrs=['bold'])
    else:
        return colored('LN', 'white', attrs=['dark'])
    
def determine_reference(sample):
    mapping = json.loads(rkvs.get('BMM:reference:mapping').decode('utf-8'))
    slot  = round((sample['ref'].RBV) / (-15)) % 24 + 1
    refx = sample['refx'].RBV
    if abs(refx - float(rkvs.get('BMM:ref:outer'))) <5:
        ring = 0
    else:
        ring = 1
    for k in mapping.keys():
        if mapping[k][0] == ring and mapping[k][1] == slot and 'empty' not in k:
            return mapping[k][2]
    return 'None'

def remaining():
    elapsed = (datetime.datetime.timestamp(datetime.datetime.now()) - float(rkvs.get('BMM:scan:starttime').decode('utf8')))
    try:
        estimate = float(rkvs.get('BMM:scan:estimated'))
    except:
        return ''
    if estimate == 0:
        return ''
    rem = estimate - elapsed
    if rem < 0:
        return '(almost done)'
    minutes = int(rem/60.)
    seconds = round(rem - minutes*60)
    return f'({minutes} min, {seconds} sec)'

