
import xraylib
run_report(__file__)

PERIODIC_TABLE = '\
H                                                                                            He \
Li Be                                                                          B  C  N  O  F Ne \
Na Mg                                                                         Al Si  P  S Cl Ar \
K  Ca                                           Sc Ti  V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr \
Rb Sr                                            Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te  I Xe \
Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W  Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn \
Fr Ra Ac Th Pa U  Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Ha Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og \
'

ELEMENTS = dict()
for i,el in enumerate(PERIODIC_TABLE.split()):
    ELEMENTS[el] = i+1
    ELEMENTS[str(i+1)] = el
 
EDGES = {'0': 'K',  'K': '0', 
         '1': 'L1', 'L1': '1',
         '2': 'L2', 'L2': '2',
         '3': 'L3', 'L3': '3',
         '4': 'M1', 'M1': '4',
         '5': 'M2', 'M2': '5',
         '6': 'M3', 'M3': '6',
         '7': 'M4', 'M4': '7',
         '8': 'M5', 'M5': '8', }


def Z_number(element):
    if str(element).capitalize() not in ELEMENTS:
        return None
    if type(element) is str:
        element = ELEMENTS[element.capitalize()]
    return element

def edge_number(edge):
    if str(edge).capitalize() not in EDGES:
        return None
    if type(edge) is str:
        edge = EDGES[edge.capitalize()]
    return edge
        
def edge_energy(element, edge):
    element = Z_number(element)
    if element is None: return None
    edge = edge_number(edge)
    if edge is None: return None
    return xraylib.EdgeEnergy(int(element), int(edge))*1000
    
