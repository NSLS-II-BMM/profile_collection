import os, json

from bluesky.plan_stubs import null, sleep, mv, mvr

from BMM.periodictable import edge_energy, Z_number, element_symbol
from BMM.logging       import BMM_log_info, report
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


class ROI():
    '''A simple class for managing the Struck ROI channels.

    Examples
    --------

    Configure the ROIs:

    >>> rois.set('Mn Fe Cu')

    Configure one ROI channel:
       
    >>> rois.set_roi(1, 'Mn')

    Choose an ROI channel:
       
    >>> rois.select('Mn')

    Print ROI configuration to the screen:
       
    >>> rois.show()
    '''
    def __init__(self):
        self.slots = [None, None, None]
        self.trigger = False

    def myprint(self, string):
        if user_ns['with_xspress3'] is False:
            print(string)
        
    def unset(self):
        self.slots = [None, None, None]
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            user = json.load(open(jsonfile))
            if 'rois' in user:
                del user['rois']
                os.chmod(jsonfile, 0o644)
                with open(jsonfile, 'w') as outfile:
                    json.dump(user, outfile)
                os.chmod(jsonfile, 0o444)
    
    def set_roi(self, i, el):
        '''Configure an ROI channel i ∈ (1 .. 3) for element el'''
        if Z_number(el) is None:
            self.slots[i-1] = None
        else:
            self.slots[i-1] = element_symbol(el)
        if user_ns['with_xspress3'] is False:
            BMM_log_info('Set ROI channel %d to %s' % (i, str(self.slots[i-1])))

    def set(self, elements):
        '''Configure the ROI channels so that an energy change knows which channel to use.

        Parameters
        ----------
        elements : list of str
            a list of 3 elements, top to bottom in the SCAs if the list is a space separated string, it will be split into a list
        '''
        if type(elements) is str:
            elements = elements.split()
        if len(elements) != 3:
            self.myprint(error_msg('\nThe list of rois must have three elements\n'))
            return()
        for i in range(3):
            self.set_roi(i+1, elements[i])
        vor, BMMuser = user_ns['vor'], user_ns['BMMuser']
        vor.channel_names(*elements)
        BMMuser.rois = elements
        self.myprint(self.show())
        ########################################################
        # save the ROI configuration to the user serialization #
        ########################################################
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            user = dict()
            if os.path.isfile(jsonfile):
                user = json.load(open(jsonfile))
            user['rois'] = ' '.join(map(str, elements))
            os.chmod(jsonfile, 0o644)
            with open(jsonfile, 'w') as outfile:
                json.dump(user, outfile)
            os.chmod(jsonfile, 0o444)

    def select_plan(self, el):
        '''Choose the ROI configured for element el'''
        if type(el) is int:
            if el < 1 or el > 3:
                self.myprint(error_msg('\n%d is not a valid ROI channel\n' % el))
                return(yield from null())
            el = self.slots[el-1]
        if el is None:
            self.myprint(error_msg('\nThat ROI is not configured\n'))
            return(yield from null())
        if Z_number(el) is None:
            self.myprint(error_msg('\n%s is not an element\n' % el))
            return(yield from null())
        selected = False
        vor = user_ns['vor']
        BMMuser = user_ns['BMMuser']
        for i in range(3):
            if element_symbol(el) == self.slots[i]:
                BMMuser.roi_channel = i+1
                if i == 0:      # help out the best effort callback
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI1', 'ROI2', 'ROI3', 'ROI4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC1', 'DTC2', 'DTC3', 'DTC4')
                    vor.set_hints(1)
                elif i == 1:
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI2_1', 'ROI2_2', 'ROI2_3', 'ROI2_4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC2_1', 'DTC2_2', 'DTC2_3', 'DTC2_4')
                    vor.set_hints(2)
                elif i == 2:
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI3_1', 'ROI3_2', 'ROI3_3', 'ROI3_4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC3_1', 'DTC3_2', 'DTC3_3', 'DTC3_4')
                    vor.set_hints(3)
                report('Set ROI channel to %s at channel %d' % (el.capitalize(), i+1))
                selected = True
        if not selected:
            self.myprint(whisper('%s is not in a configured channel, not changing BMMuser.roi_channel' % el.capitalize()))
            yield from null()

    def select(self, el):
        '''Choose the ROI configured for element el'''
        if type(el) is int:
            if el < 1 or el > 3:
                self.myprint(error_msg('\n%d is not a valid ROI channel\n' % el))
                return
            el = self.slots[el-1]
        if el is None:
            self.myprint(error_msg('\nThat ROI is not configured\n'))
            return
        if Z_number(el) is None:
            self.myprint(error_msg('\n%s is not an element\n' % el))
            return
        selected = False
        vor = user_ns['vor']
        BMMuser = user_ns['BMMuser']
        for i in range(3):
            if element_symbol(el) == self.slots[i]:
                BMMuser.roi_channel = i+1
                if i == 0:      # help out the best effort callback
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI1', 'ROI2', 'ROI3', 'ROI4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC1', 'DTC2', 'DTC3', 'DTC4')
                    vor.set_hints(1)
                elif i == 1:
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI2_1', 'ROI2_2', 'ROI2_3', 'ROI2_4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC2_1', 'DTC2_2', 'DTC2_3', 'DTC2_4')
                    vor.set_hints(2)
                elif i == 2:
                    (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI3_1', 'ROI3_2', 'ROI3_3', 'ROI3_4')
                    (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC3_1', 'DTC3_2', 'DTC3_3', 'DTC3_4')
                    vor.set_hints(3)
                report('Set ROI channel to %s at channel %d' % (el.capitalize(), i+1))
                selected = True
        if not selected:
            self.myprint(whisper('%s is not in a configured channel, not changing BMMuser.roi_channel' % el.capitalize()))

            
# 22.265
            
    def show(self):
        '''Show configuration of ROI channels'''
        BMMuser = user_ns['BMMuser']
        text = 'Analog ROI channels:\n'
        for i in range(3):
            if i+1 == BMMuser.roi_channel:
                text +='      ROI %d : %s\n'% (i+1, go_msg(str(self.slots[i])))
            else:
                text +='      ROI %d : %s\n'% (i+1, str(self.slots[i]))
        return text
    


