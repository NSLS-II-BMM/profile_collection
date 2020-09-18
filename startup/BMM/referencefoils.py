import os, json

from BMM.periodictable import edge_energy, Z_number, element_symbol

class ReferenceFoils():
    '''A simple class for managing the reference foil holder.

    Examples
    --------
    Configure reference holder:
      
    >>> foils.set('Mn Fe Cu Zn Pb')

    Configure one slot of the reference holder:
       
    >>> foils.set_slot(2, 'Fe')

    Return the xafs_linxs value for a slot:
       
    >>> pos = foils.position(2)

    Move to a slot by element symbol:
       
    >>> RE(foils.move('Fe'))
    >>> yield from foils.move('Fe')

    Print foils configuration to the screen:
       
    >>> print(foils.show())
    '''
    def __init__(self):
        self.slots = [None, None, None, None, None]

    def unset(self):
        self.slots = [None, None, None, None, None]
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            user = json.load(open(jsonfile))
            if 'foils' in user:
                del user['foils']
                os.chmod(jsonfile, 0o644)
                with open(jsonfile, 'w') as outfile:
                    json.dump(user, outfile)
                os.chmod(jsonfile, 0o444)

    def set_slot(self, i, el):
        '''Configure a slot i ∈ (0 .. 4) for element el'''
        if Z_number(el) is None:        
            self.slots[i-1] = None
        else:
            self.slots[i-1] = element_symbol(el)
        BMM_log_info('Set reference slot %d to %s' % (i, str(self.slots[i-1])))

    def set(self, elements):
        '''Configure the foils so that an energy change knows where to put the
        reference stage.

        Parameters
        ----------
        elements: list of str
            a list of 5 foils, top to bottom in the foil holder if the list is a space separated string, it will be split into a list
        '''
        if type(elements) is str:
            elements = elements.split()
        if len(elements) != 5:
            print(error_msg('\nThe list of foils must have five elements\n'))
            return()
        for i in range(5):
            self.set_slot(i+1, elements[i])
        print(self.show())
        #########################################################
        # save the foil configuration to the user serialization #
        #########################################################
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        user = dict()
        if os.path.isfile(jsonfile):
            user = json.load(open(jsonfile))
            user['foils'] = ' '.join(map(str, elements))
            os.chmod(jsonfile, 0o644)
        with open(jsonfile, 'w') as outfile:
            json.dump(user, outfile)
        os.chmod(jsonfile, 0o444)
            
        
    def position(self, i):
        '''Return the xafs_linxs position corresponding to slot i where i ∈ (0 .. 4)'''
        if type(i) is str and i in foils.slots:
            i=foils.slots.index(i.capitalize())
        if type(i) is not int: return xafs_linxs.user_readback.get() # so it doesn't move...
        if i > 4:        return 90
        if i < 0:        return -90
        return(-90 + i*45)

    def move(self, el):
        '''Move to the slot configured for element el'''
        if type(el) is int:
            if el < 1 or el > 5:
                print(error_msg('\n%d is not a valid foil slot\n' % el))
                return(yield from null())
            el = self.slots[el-1]
        if el is None:
            print(error_msg('\nThat slot is empty\n'))
            return(yield from null())
        el = el.capitalize()
        if Z_number(el) is None:
            print(error_msg('\n%s is not an element\n' % el))
            return(yield from null())
        moved = False
        for i in range(5):
            if element_symbol(el) == self.slots[i]:
                yield from mv(xafs_linxs, self.position(i))
                report('Moved xafs_linxs to %s at slot %d' % (el.capitalize(), i+1))
                moved = True
        if not moved:
            print(warning_msg('%s is not in the reference holder, not moving xafs_linxs' % el.capitalize()))
            yield from null()
            
    def show(self):
        '''Show configuration of foil holder'''
        text = ' Reference foils (xafs_linxs):\n'
        for i in range(5):
            ast = ' '
            if abs(self.position(i) - xafs_linxs.user_readback.get()) < 1:
                ast = '*'
            text += '      slot %d : %s at %d mm\n'% (i+1, str(self.slots[i]), self.position(i))
        return(text)
            


# ## if this startup file is "%run -i"-ed, then need to reset
# ## foils to the serialized configuration
# jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
# if os.path.isfile(jsonfile):
#     user = json.load(open(jsonfile))
#     if 'foils' in user:
#         foils.set(user['foils'])
# ## else if starting bsui fresh, perform the delayed foil configuration
# if BMMuser.read_foils is not None:
#     foils.set(BMMuser.read_foils)
#     BMMuser.read_foils = None
