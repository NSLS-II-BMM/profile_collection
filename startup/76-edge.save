import time
import json

from BMM.periodictable import edge_energy, Z_number, element_symbol

run_report(__file__)

# class ReferenceFoils():
#     '''A simple class for managing the reference foil holder.

#     Configure reference holder:
#        foils.set('Mn Fe Cu Zn Pb')

#     Configure one slot of the reference holder:
#        foils.set_slot(2, 'Fe')

#     Return the xafs_linxs value for a slot:
#        pos = foils.position(2)

#     Move to a slot by element symbol:
#        RE(foils.move('Fe'))
#        yield from foils.move('Fe')

#     Print foils configuration to the screen:
#        print(foils.show())
#     '''
#     def __init__(self):
#         self.slots = [None, None, None, None, None]

#     def unset(self):
#         self.slots = [None, None, None, None, None]
#         jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
#         if os.path.isfile(jsonfile):
#             user = json.load(open(jsonfile))
#             if 'foils' in user:
#                 del user['foils']
#                 os.chmod(jsonfile, 0o644)
#                 with open(jsonfile, 'w') as outfile:
#                     json.dump(user, outfile)
#                 os.chmod(jsonfile, 0o444)

#     def set_slot(self, i, el):
#         '''Configure a slot i ∈ (0 .. 4) for element el'''
#         if Z_number(el) is None:        
#             self.slots[i-1] = None
#         else:
#             self.slots[i-1] = element_symbol(el)
#         BMM_log_info('Set reference slot %d to %s' % (i, str(self.slots[i-1])))

#     def set(self, elements):
#         '''Configure the foils so that an energy change knows where to put the
#         reference stage.

#         Input:
#           elements: a list of 5 foils, top to bottom in the foil holder
#                     if the list is a space separated string, it will be split into a list
#         '''
#         if type(elements) is str:
#             elements = elements.split()
#         if len(elements) != 5:
#             print(error_msg('\nThe list of foils must have five elements\n'))
#             return()
#         for i in range(5):
#             self.set_slot(i+1, elements[i])
#         print(self.show())
#         #########################################################
#         # save the foil configuration to the user serialization #
#         #########################################################
#         jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
#         user = dict()
#         if os.path.isfile(jsonfile):
#             user = json.load(open(jsonfile))
#             user['foils'] = ' '.join(map(str, elements))
#             os.chmod(jsonfile, 0o644)
#         with open(jsonfile, 'w') as outfile:
#             json.dump(user, outfile)
#         os.chmod(jsonfile, 0o444)
            
        
#     def position(self, i):
#         '''Return the xafs_linxs position corresponding to slot i where i ∈ (0 .. 4)'''
#         if type(i) is str and i in foils.slots:
#             i=foils.slots.index(i.capitalize())
#         if type(i) is not int: return xafs_linxs.user_readback.get() # so it doesn't move...
#         if i > 4:        return 90
#         if i < 0:        return -90
#         return(-90 + i*45)

#     def move(self, el):
#         '''Move to the slot configured for element el'''
#         if type(el) is int:
#             if el < 1 or el > 5:
#                 print(error_msg('\n%d is not a valid foil slot\n' % el))
#                 return(yield from null())
#             el = self.slots[el-1]
#         if el is None:
#             print(error_msg('\nThat slot is empty\n'))
#             return(yield from null())
#         el = el.capitalize()
#         if Z_number(el) is None:
#             print(error_msg('\n%s is not an element\n' % el))
#             return(yield from null())
#         moved = False
#         for i in range(5):
#             if element_symbol(el) == self.slots[i]:
#                 yield from mv(xafs_linxs, self.position(i))
#                 report('Moved xafs_linxs to %s at slot %d' % (el.capitalize(), i+1))
#                 moved = True
#         if not moved:
#             print(warning_msg('%s is not in the reference holder, not moving xafs_linxs' % el.capitalize()))
#             yield from null()
            
#     def show(self):
#         '''Show configuration of foil holder'''
#         text = ' Reference foils (xafs_linxs):\n'
#         for i in range(5):
#             ast = ' '
#             if abs(self.position(i) - xafs_linxs.user_readback.get()) < 1:
#                 ast = '*'
#             text += '      slot %d : %s at %d mm\n'% (i+1, str(self.slots[i]), self.position(i))
#         return(text)
            
# foils = ReferenceFoils()
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



# class ROI():
#     '''A simple class for managing the Struck ROI channels.

#     Configure the ROIs:
#        rois.set('Mn Fe Cu')

#     Configure one ROI channel:
#        rois.set_roi(1, 'Mn')

#     Choose an ROI channel:
#        rois.select('Mn')

#     Print ROI configuration to the screen:
#        rois.show()
#     '''
#     def __init__(self):
#         self.slots = [None, None, None]

#     def unset(self):
#         self.slots = [None, None, None]
#         jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
#         if os.path.isfile(jsonfile):
#             user = json.load(open(jsonfile))
#             if 'rois' in user:
#                 del user['rois']
#                 os.chmod(jsonfile, 0o644)
#                 with open(jsonfile, 'w') as outfile:
#                     json.dump(user, outfile)
#                 os.chmod(jsonfile, 0o444)
    
#     def set_roi(self, i, el):
#         '''Configure an ROI channel i ∈ (1 .. 3) for element el'''
#         if Z_number(el) is None:
#             self.slots[i-1] = None
#         else:
#             self.slots[i-1] = element_symbol(el)
#         BMM_log_info('Set ROI channel %d to %s' % (i, str(self.slots[i-1])))

#     def set(self, elements):
#         '''Configure the ROI channels so that an energy change knows which channel to use.

#         Input:
#           elements: a list of 3 elements, top to bottom in the SCAs
#                     if the list is a space separated string, it will be split into a list
#         '''
#         if type(elements) is str:
#             elements = elements.split()
#         if len(elements) != 3:
#             print(error_msg('\nThe list of foils must have three elements\n'))
#             return()
#         for i in range(3):
#             self.set_roi(i+1, elements[i])
#         vor.channel_names(*elements)
#         print(self.show())
#         ########################################################
#         # save the ROI configuration to the user serialization #
#         ########################################################
#         jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
#         if os.path.isfile(jsonfile):
#             user = dict()
#             if os.path.isfile(jsonfile):
#                 user = json.load(open(jsonfile))
#             user['rois'] = ' '.join(map(str, elements))
#             os.chmod(jsonfile, 0o644)
#             with open(jsonfile, 'w') as outfile:
#                 json.dump(user, outfile)
#             os.chmod(jsonfile, 0o444)

#     def select(self, el):
#         '''Choose the ROI configured for element el'''
#         if type(el) is int:
#             if el < 1 or el > 3:
#                 print(error_msg('\n%d is not a valid ROI channel\n' % el))
#                 return(yield from null())
#             el = self.slots[el-1]
#         if el is None:
#             print(error_msg('\nThat ROI is not configured\n'))
#             return(yield from null())
#         if Z_number(el) is None:
#             print(error_msg('\n%s is not an element\n' % el))
#             return(yield from null())
#         selected = False
#         for i in range(3):
#             if element_symbol(el) == self.slots[i]:
#                 BMMuser.roi_channel = i+1
#                 if i == 0:      # help out the best effort callback
#                     (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI1', 'ROI2', 'ROI3', 'ROI4')
#                     (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC1', 'DTC2', 'DTC3', 'DTC4')
#                     vor.set_hints(1)
#                 elif i == 1:
#                     (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI2_1', 'ROI2_2', 'ROI2_3', 'ROI2_4')
#                     (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC2_1', 'DTC2_2', 'DTC2_3', 'DTC2_4')
#                     vor.set_hints(2)
#                 elif i == 2:
#                     (BMMuser.roi1, BMMuser.roi2, BMMuser.roi3, BMMuser.roi4) = ('ROI3_1', 'ROI3_2', 'ROI3_3', 'ROI3_4')
#                     (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4) = ('DTC3_1', 'DTC3_2', 'DTC3_3', 'DTC3_4')
#                     vor.set_hints(3)
#                 report('Set ROI channel to %s at channel %d' % (el.capitalize(), i+1))
#                 selected = True
#         if not selected:
#             print(warning_msg('%s is not in a configured channel, not changing BMMuser.roi_channel' % el.capitalize()))
#             yield from null()

# # 22.265
            
#     def show(self):
#         '''Show configuration of ROI channels'''
#         text = ' ROI channels:\n'
#         for i in range(3):
#             if i+1 == BMMuser.roi_channel:
#                 text +='      ROI %d : %s\n'% (i+1, go_msg(str(self.slots[i])))
#             else:
#                 text +='      ROI %d : %s\n'% (i+1, str(self.slots[i]))
#         return text

# rois = ROI()
# ## if this startup file is "%run -i"-ed, then need to reset
# ## foils to the serialized configuration
# jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
# if os.path.isfile(jsonfile):
#     user = json.load(open(jsonfile))
#     if 'rois' in user:
#         rois.set(user['rois'])
#         BMMuser.read_rois = None
# ## else if starting bsui fresh, perform the delayed foil configuration
# if BMMuser.read_rois is not None:
#     rois.set(BMMuser.read_rois)
#     BMMuser.read_foils = None



        

    
def approximate_pitch(energy):
    if dcm._crystal is '111':
        m = -4.57145e-06
        b = 4.04782 + 0.0303    # ad hoc correction....
        return(m*energy + b)
    else:
        m = -2.7015e-06
        b = 2.38638
        return(m*energy + b)
        

def show_edges():
    #text = foils.show() + '\n' + rois.show()
    text = show_reference_wheel() + '\n' + rois.show()
    boxedtext('Foils and ROIs configuration', text[:-1], 'brown', width=85)
    
def change_edge(el, focus=False, edge='K', energy=None, slits=True, target=300., xrd=False, bender=True):
    '''Change edge energy by:
       1. Moving the DCM above the edge energy
       2. Moving the photon delivery system to the correct mode
       3. Running a rocking curve scan
       4. --(Running a slits_height scan)--
       5. Moving the reference holder to the correct slot

    Input:
       el:     (string) one- or two-letter symbol
       focus:  (Boolean) T=focused or F=unfocused beam         [False, unfocused]
       edge:   (string) edge symbol                            ['K']
       energy: (float) e0 value                                [None, determined from el/edge]
       slits:  (Boolean) perform slit_height() scan            [False]
       target: (float) energy where rocking curve is measured  [300]
       xrd:    (Boolean) force photon delivery system to XRD   [False]

    Examples:

    Normal use, unfocused beam:
       RE(change_edge('Fe'))

    Normal use, focused beam:
       RE(change_edge('Fe', focus=True))

    L2 or L1 edge:
       RE(change_edge('Re', edge='L2'))

    Measure rocking curve at edge energy:
       RE(change_edge('Fe', target=0))

    XRD, new energy:
       RE(change_edge('Fe', xrd=True, energy=8600))
           note that you must specify an element, but it doesn't matter which one
           the energy will be moved to the specified energy
           xrd=True implies focus=True and target=0
    '''
    #BMMuser.prompt = True
    el = el.capitalize()
    
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than changing to the %s edge.\n' %
                       (BMMuser.macro_sleep, el)))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting change_edge() macro....\n'))
        return(yield from null())
    
    if energy is None:
        energy = edge_energy(el,edge)
        
    if energy is None:
        print(error_msg('\nEither %s or %s is not a valid symbol\n' % (el, edge)))
        return(yield from null())
    if energy > 23500:
        edge = 'L3'
        energy = edge_energy(el,'L3')

    if energy < 4950:
        print(warning_msg('The %s edge energy is below 4950 eV' % el))
        print(warning_msg('You have to change energy by hand.'))
        return(yield from null())

    if energy > 23500:
        print(warning_msg('The %s edge energy is outside the range of this beamline!' % el))
        return(yield from null())

    BMMuser.edge        = edge
    BMMuser.element     = el
    BMMuser.edge_energy = energy

    if energy > 8000:
        mode = 'A' if focus else 'D'
    elif energy < 6000:
        #mode = 'B' if focus else 'F'   ## mode B currently is inaccessible :(
        mode = 'C' if focus else 'F'
    else:
        mode = 'C' if focus else 'E'
    if xrd:
        mode   = 'XRD'
        focus  = True
        target = 0.0
    current_mode = get_mode()

    ################################
    # confirm configuration change #
    ################################
    print(bold_msg('\nEnergy change:'))
    print('   %s: %s %s' % (list_msg('edge'),                    el.capitalize(), edge.capitalize()))
    print('   %s: %.1f'  % (list_msg('edge energy'),             energy))
    print('   %s: %.1f'  % (list_msg('target energy'),           energy+target))
    print('   %s: %s'    % (list_msg('focus'),                   str(focus)))
    print('   %s: %s'    % (list_msg('photon delivery mode'),    mode))
    print('   %s: %s'    % (list_msg('optimizing slits height'), str(slits)))
    if BMMuser.prompt:
        action = input("\nBegin energy change? [Y/n then Enter] ")
        if action.lower() == 'q' or action.lower() == 'n':
            return(yield from null())
        if mode == 'C' and energy < 6000:
            print(warning_msg('\nMoving to mode C for focused beam and an edge energy below 6 keV.'))
            action = input("You will not get optimal harmonic rejection.  Continue anyway?  [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                return(yield from null())
        
    start = time.time()
    BMM_log_info('Configuring beamline for %s edge' % el)
    yield from dcm.kill_plan()
    ###################################
    # move the DCM to target eV above #
    ###################################
    # print('Moving mono to energy %.1f eV...' % (energy+target))
    # yield from mv(dcm.energy, energy+target)

    ################################################
    # change to the correct photon delivery mode   #
    #      + move mono to correct energy           #
    #      + move reference holder to correct slot #
    ################################################
    # if not calibrating and mode != current_mode:
    #     print('Moving to photon delivery mode %s...' % mode)
    yield from change_mode(mode=mode, prompt=False, edge=energy+target, reference=el, bender=bender)
    yield from kill_mirror_jacks()
    yield from sleep(1)
    if BMMuser.motor_fault is not None:
        print(error_msg('\nSome motors are reporting amplifier faults: %s' % BMMuser.motor_fault))
        print('Clear the faults and try running the same change_edge() command again.')
        print('Troubleshooting: ' + url_msg('https://nsls-ii-bmm.github.io/BeamlineManual/trouble.html#amplifier-fault'))
        BMMuser.motor_fault = None
        return(yield from null())
    BMMuser.motor_fault = None
    
        
    ############################
    # run a rocking curve scan #
    ############################
    print('Optimizing rocking curve...')
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
    yield from mv(dcm_pitch, approximate_pitch(energy+target))
    yield from sleep(1)
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
    yield from rocking_curve()
    close_last_plot()
    
    ##########################
    # run a slits height scan #
    ##########################
    if slits:
        print('Optimizing slits height...')
        yield from slit_height(move=True)
        close_last_plot()
        ## redo rocking curve?

    ###################
    # set roi channel #
    ###################
    if not xrd:
        print('Moving reference foil...')
        #yield from foils.move(el)
        yield from rois.select(el)
        show_edges()
    
    print('\nYou are now ready to measure at the %s edge' % el)
    if slits is False:
        print('  * You may need to verify the slit position:  RE(slit_height())')
    BMM_log_info('Finished configuring for %s edge' % el)
    yield from dcm.kill_plan()
    end = time.time()
    print('\n\nThat took %.1f min' % ((end-start)/60))
    return()
