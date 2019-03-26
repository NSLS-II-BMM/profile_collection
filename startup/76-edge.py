import time

run_report(__file__)

class ReferenceFoils():
    '''A simple class for managing the reference foil holder.

    Configure reference holder:
       foils.set('Mn Fe Cu Zn Pb')

    Configure one slot of the reference holder:
       foils.set_slot(2, 'Fe')

    Return the xafs_ref value for a slot:
       pos = foils.position(2)

    Move to a slot by element symbol:
       foils.move('Fe')

    Print foils configuration to the screen:
       foils.show()
    '''
    def __init__(self):
        self.slots = [None, None, None, None, None]

    def set_slot(i, el):
        '''Configure a slot i ∈ (0 .. 4) for element el'''
        if Z_number(el) is None:        
            self.slots[i-1] = None
        else:
            self.slots[i-1] = element_symbol[el]
        BMM_log_info('Set reference slot %d to %s' % (i, str(self.slots[i-1])))

    def set(self, elements):
        '''Configure the foils so that an energy change knows where to put the
        reference stage.

        Input:
          elements: a list of 5 foils, top to bottom in the foil holder
                    if the list is a space separated string, it will be split into a list
        '''
        if type(elements) is str:
            elements = element.split()
        if len(elements) != 5:
            print(error_msg('\nThe list of foils must have five elements\n'))
            return()
        for i in range(5):
            foils.set_slot(i+1, elements[i])
        foils.show()
        ## perhaps write this to the user serialization file....
        return()
        
        
    def position(self, i):
        '''Return the xafs_ref position corresponding to slot i where i ∈ (0 .. 4)'''
        if i is not int: return xafs_ref.user_readback.value # so it doesn't move...
        if i > 4:        return 90
        if i < 0:        return -90
        return -90 + i*45

    def move(self, el):
        '''Move to the slot configured for element el'''
        if Z_number(el) is None:
            print(error_msg('\n%s is not a valid element (foils.move())\n' % el.capitalize()))
            return(yield from null())
        moved = False
        for i in range(5):
            if element_symbol(el) == self.slots[i]:
                yield from mv(xafs_ref, self.position(i))
                report('Moved xafs_ref to %s at slot %d' % (el.capitalize(), i+1))
                #print('Moved xafs_ref to %s at slot %d' % (el.capitalize(), i+1))
                #BMM_log_info('Moved xafs_ref to %s at slot %d' % (el, i+1))
                moved = True
        if not moved:
            print(warning_msg('%s is not in the reference holder, not moving xafs_ref' % el.capitalize()))
            yield from null()
            
    def show(self):
        '''Show configuration of foil holder'''
        print('Reference foils:')
        for i in range(5):
            print('\tslot %d : %s at %d mm'% (i+1, str(self.slots[i]), self.position(i)))
            
foils = ReferenceFoils()


def change_edge(el, focus=False, edge='K', energy=None, slit=False):
    '''Change edge energy by:
       1. Moving the DCM to 50 eV above the edge energy
       2. Moving the photon delivery system to the correct mode
       3. Running a rocking curve scan
       4. --(Running a slit_height scan)--
       5. Moving the reference holder to the correct slot

    Input:
       el:     (string) one- or two-letter symbol
       focus:  (Boolean) T=focused or F=unfocused beam  [False, unfocused]
       edge:   (string) edge symbol                     ['K']
       energy: (float) e0 value                         [None, determined from el/edge]
       slit:   (Boolean) perform slit_height() scan     [False]
    '''
    if energy is None:
        energy = edge_energy(el,edge)
        
    if energy = None:
        print(error_msg('\n%s is not a valid element\n' % e))
        return(yield from null())
    if energy > 23500:
        energy = edge_energy(el,'L3')

    if energy < 4950:
        print(warning_msg('The %s edge energy is below 4950 eV' % el))
        print(warning_msg('You have to change energy by hand.'))
        return(yield from null())

    if energy > 23500:
        print(warning_msg('The %s edge energy is outside the range of this beamline!' % el))
        return(yield from null())

    BMM_config.edge        = edge
    BMM_config.element     = el
    BMM_config.edge_energy = energy

    if energy > 8000:
        mode = 'A' if focus else 'D'
    elif: energy < 6000:
        mode = 'B' if focus else 'F'
    else:
        mode = 'C' if focus else 'E'
    current_mode = get_mode()

    #########################
    # confirm energy change #
    #########################
    print('\nEnergy change:')
    print('\tedge: %s %s' % (el.capitalize(), edge.capitalize()))
    print('\tenergy: %.1f' % energy)
    print('\tfocus: %s' % str(focus))
    print('\tphoton delivery mode: %s' % mode)
    print('\toptimizing slit height: %s' % str(slit))
    action = input("\nBegin energy change? [Y/n then Enter] ")
    if action.lower() == 'q' or action.lower() == 'n':
        return(yield from null())

    if True:
        return(yield from null())
    
    start = time.time()
    BMM_log_info('Configuring beamline for %s edge' % el)
    ###############################
    # move the DCM to 50 eV above #
    ###############################
    print('Moving mono to energy %.1f eV...' % energy+50)
    yield from mv(dcm.energy, energy+50)

    ##############################################
    # change to the correct photon delivery mode #
    ##############################################
    if mode != current_mode:
        print('Moving to photon delivery mode %s...' % mode)
        yield from change_mode(mode)

    ############################
    # run a rocking curve scan #
    ############################
    print('Optimizing rocking curve...')
    yield from rocking_curve()

    ##########################
    # run a slit height scan #
    ##########################
    if slit:
        print('Optimizing slit height...')
        yield from slit_height()
        ## redo rocking curve?

    ######################################
    # move to the correct reference slot #
    ######################################
    print('Moving reference foil...')
    yield from foils.move(el)
    
    print('You are now ready to measure at the %s edge' % el)
    print('Two things that are not done automagically:')
    print('  1. You may need to verify the slit position:  RE(slit_height())')
    print('  2. If measuring fluorescence, remember to adjust the cables')
    BMM_log_info('Finished configuring for %s edge' % el)
    end = time.time()
    print(end-start + ' elapsed')
    return()
