from bluesky.plan_stubs import null, abs_set, sleep, mv, mvr

from bluesky_queueserver.manager.profile_tools import set_user_ns

## from IPython import get_ipython
## user_ns = get_ipython().user_ns


class attenuator():
    def __init__(self):
        self.motor = None
        
    def set_position(self, index):
        if self.motor is None:
            return(yield from null());
        if index == 0:
            yield from mv(self.motor,  55)
        elif index == 1:
            yield from mv(self.motor, -46.5)
        elif index == 2:
            yield from mv(self.motor, -20.5)
        elif index == 3:
            yield from mv(self.motor,  5.5)
        elif index == 4:
            yield from mv(self.motor,  31)


@set_user_ns
def filter_state(user_ns):
    BMMuser = user_ns['BMMuser']
    states = ['Both filters are out of the beam',
              'Filter 1: 100 μm, Filter 2: out, total: 100  μm',
              'Filter 1: 200 μm, Filter 2: out, total: 200  μm',
              'Filter 1: 200 μm, Filter 2: 100 μm, total: 300  μm',
              'Filter 1: 200 μm, Filter 2: 200 μm, total: 400  μm',
              'Filter 1: 500 μm, Filter 2: out, total: 500  μm',
              'Filter 1: 500 μm, Filter 2: 100 μm, total: 600  μm',
              'Filter 1: 500 μm, Filter 2: 200 μm, total: 700  μm',
              'Filter 1: 500 μm, Filter 2: 500 μm, total: 1000  μm',
              'Filter 1: 1700 μm, Filter 2: out, total: 1700  μm',
              'Filter 1: 1700 μm, Filter 2: 100 μm, total: 1800  μm',
              'Filter 1: 1700 μm, Filter 2: 200 μm, total: 1900  μm',
              'Filter 1: 1700 μm, Filter 2: 500 μm, total: 2200  μm',
              'Filter 1: 1700 μm, Filter 2: 1700 μm, total:2400  μm',
        ]
    print(states[BMMuser.filter_state])

@set_user_ns
def set_filters(thickness=None, state=None, user_ns):
    positions = [55, -46.5, -20.5, 5.5, 31]

    BMMuser = user_ns['BMMuser']
    if thickness == 0 or state == 0:
        yield from mv(dm1_filters1, positions[0], dm1_filters2, positions[0])
        BMMuser.filter_state = 0
    elif thickness == 100 or state == 1:
        yield from mv(dm1_filters1, positions[1], dm1_filters2, positions[0])
        BMMuser.filter_state = 1
    elif thickness == 200 or state == 2:
        yield from mv(dm1_filters1, positions[2], dm1_filters2, positions[0])
        BMMuser.filter_state = 2
    elif thickness == 300 or state == 3:
        yield from mv(dm1_filters1, positions[2], dm1_filters2, positions[1])
        BMMuser.filter_state = 3
    elif thickness == 400 or state == 4:
        yield from mv(dm1_filters1, positions[2], dm1_filters2, positions[2])
        BMMuser.filter_state = 4
    elif thickness == 500 or state == 5:
        yield from mv(dm1_filters1, positions[3], dm1_filters2, positions[0])
        BMMuser.filter_state = 5
    elif thickness == 600 or state == 6:
        yield from mv(dm1_filters1, positions[3], dm1_filters2, positions[1])
        BMMuser.filter_state = 6
    elif thickness == 700 or state == 7:
        yield from mv(dm1_filters1, positions[3], dm1_filters2, positions[2])
        BMMuser.filter_state = 7
    elif thickness == 1000 or state == 8:
        yield from mv(dm1_filters1, positions[3], dm1_filters2, positions[3])
        BMMuser.filter_state = 8
    elif thickness == 1700 or state == 9:
        yield from mv(dm1_filters1, positions[4], dm1_filters2, positions[0])
        BMMuser.filter_state = 9
    elif thickness == 1800 or state ==10:
        yield from mv(dm1_filters1, positions[4], dm1_filters2, positions[1])
        BMMuser.filter_state = 10
    elif thickness == 1900 or state == 11:
        yield from mv(dm1_filters1, positions[4], dm1_filters2, positions[2])
        BMMuser.filter_state = 11
    elif thickness == 2200 or state == 12:
        yield from mv(dm1_filters1, positions[4], dm1_filters2, positions[3])
        BMMuser.filter_state = 12
    elif thickness == 3400 or state == 13:
        yield from mv(dm1_filters1, positions[4], dm1_filters2, positions[4])
        BMMuser.filter_state = 13
    else:
        print(error_msg('Valid filter thicknesses are: '))
        print(error_msg('    state  0: 0 μm'))
        print(error_msg('    state  1: 100 μm'))
        print(error_msg('    state  2: 200 μm'))
        print(error_msg('    state  3: 300 μm'))
        print(error_msg('    state  4: 400 μm'))
        print(error_msg('    state  5: 500 μm'))
        print(error_msg('    state  6: 600 μm'))
        print(error_msg('    state  7: 700 μm'))
        print(error_msg('    state  8: 1000 μm'))
        print(error_msg('    state  9: 1700 μm'))
        print(error_msg('    state 10: 1800 μm'))
        print(error_msg('    state 11: 1900 μm'))
        print(error_msg('    state 12: 2200 μm'))
        print(error_msg('    state 13: 3400 μm'))
        yield from null()
            
