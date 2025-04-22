import re
from BMM.macrobuilder import BMMMacroBuilder
from ophyd import EpicsSignal

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


class ResonantReflectivityMacroBuilder(BMMMacroBuilder):
    '''A class for parsing specially constructed spreadsheets and
    generating macros for measuring resonant reflectivity.

    Examples
    --------
    >>> refl = ResonantReflectivityMacroBuilder()
    >>> refl.spreadsheet('refl.xlsx')
    >>> refl.write_macro()

    '''
    macro_type = 'Resonant reflectivity'


    roi2_minx  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI2:MinX',  name='')
    roi2_sizex = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI2:SizeX', name='')
    roi2_miny  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI2:MinY',  name='')
    roi2_sizey = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI2:SizeY', name='')
    roi3_minx  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI3:MinX',  name='')
    roi3_sizex = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI3:SizeX', name='')
    roi3_miny  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI3:MinY',  name='')
    roi3_sizey = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROI3:SizeY', name='')

    roistat2_minx  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:2:MinX',  name='')
    roistat2_sizex = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:2:SizeX', name='')
    roistat2_miny  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:2:MinY',  name='')
    roistat2_sizey = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:2:SizeY', name='')
    roistat3_minx  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:3:MinX',  name='')
    roistat3_sizex = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:3:SizeX', name='')
    roistat3_miny  = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:3:MinY',  name='')
    roistat3_sizey = EpicsSignal('XF:06BMB-ES{Det:PIL100k}:ROIStat1:3:SizeY', name='')

    
    def screen_rois(self):
        roistat2_minx.put(roi2_minx.get())
        roistat2_sizex.put(roi2_sizex.get())
        roistat2_miny.put(roi2_miny.get())
        roistat2_sizey.put(roi2_sizey.get())
        roistat3_minx.put(roi3_minx.get())
        roistat3_sizex.put(roi3_sizex.get())
        roistat3_miny.put(roi3_miny.get())
        roistat3_sizey.put(roi3_sizey.get())

        print('Cut-n-paste these ROI values into your spreadsheet.\n')
        print(f'ROI2: {roi2_minx.get()} {roi2_sizex.get()} {roi2_miny.get()} {roi2_sizey.get()}')
        print(f'ROI3: {roi3_minx.get()} {roi3_sizex.get()} {roi3_miny.get()} {roi3_sizey.get()}')


    def set_rois(self, which, values):
        if which.lower() == 'roi2':
            mx, sz, my, sy = values # .split()
            roistat2_minx.put(mx)
            roi2_minx.put(mx)
            roistat2_sizex.put(sx)
            roi2_sizex.put(sx)
            roistat2_miny.put(my)
            roi2_miny.put(my)
            roistat2_sizey.put(sy)
            roi2_sizey.put(sy)
        elif which.lower() == 'roi3':
            mx, sz, my, sy = values # .split()
            roistat3_minx.put(mx)
            roi3_minx.put(mx)
            roistat3_sizex.put(sx)
            roi3_sizex.put(sx)
            roistat3_miny.put(my)
            roi3_miny.put(my)
            roistat3_sizey.put(sy)
            roi3_sizey.put(sy)
        else:
            print('Valid strings identifying the ROI are: roi2 roi3 ')
    
    def _write_macro(self):
        '''Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of line to move to the
        correct spinner, lines to find or move to the center-aligned
        location in pitch and Y, lines to move to and from the correct
        glancing angle value, a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.
        '''
        element, edge, focus = (None, None, None)
        self.tab = ' '*8
        count = 0


        if self.nreps > 1:
            self.content += self.tab + f'for rep in range({self.nreps}):\n\n'
            self.tab = ' '*12
            #self.do_first_change = True
            self.content += self.check_edge()
        else:
            self.content += self.check_edge() + '\n'
            

        for m in self.measurements:

            if m['default'] is True:
                element = m['element']
                edge    = m['edge']
                continue
            if self.skip_row(m) is True:
                continue

            count += 1
            if self.nreps > 1:
                self.content += self.tab + f'report(f"{self.macro_type} sequence {{{count}+{int(self.calls_to_xafs/self.nreps)}*rep}} of {self.calls_to_xafs}", level="bold", slack=True)\n'
            else:
                self.content += self.tab + f'report("{self.macro_type} sequence {count} of {self.calls_to_xafs}", level="bold", slack=True)\n'

            #######################################
            # default element/edge(/focus) values #
            #######################################
            for k in ('element', 'edge', 'focus'):
                if m[k] is None:
                    m[k] = self.measurements[0][k]

            ##########################
            # change edge, if needed #
            ##########################
            focus = False
            if m['focus'] == 'focused':
                focus = True
            text, time, inrange = self.do_change_edge(m['element'], m['edge'], focus, self.tab)
            if inrange is False: return(False)

            # if self.do_first_change is True:
            #     self.do_first_change = False
            #     self.content += text
            #     self.totaltime += time
                
            if m['element'] != element or m['edge'] != edge: # focus...
                element = m['element']
                edge    = m['edge']
                self.content += text
                self.totaltime += time
                
            else:
                if self.verbose:
                    self.content += self.tab + '## staying at %s %s\n' % (m['element'], m['edge'])
                pass

            #######################
            # move to next sample #
            #######################
            if self.nonezero(m['spinner']):
                self.content += self.tab + f'yield from ga.to({m["spinner"]})\n'
            if self.nonezero(m['samplex']):
                self.content += self.tab + f'yield from mv(xafs_x, {m["samplex"]})\n'

            ###################################
            # move to correct slit dimensions #
            ###################################
            if m['slitheight'] is not None:
                if self.check_limit(user_ns['slits3'].vsize, m['slitheight']) is False: return(False)
                self.content += self.tab + f'yield from mv(slits3.vsize, {m["slitheight"]})\n'
            if m['slitwidth'] is not None:
                if self.check_limit(user_ns['slits3'].vsize, m['slitwidth']) is False: return(False)
                self.content += self.tab + f'yield from mv(slits3.hsize, {m["slitwidth"]})\n'

            #####################################
            # move to correct detector position #
            #####################################
            if m['detectorx'] is not None:
                if self.check_limit(user_ns['xafs_detx'], m['detectorx']) is False: return(False)
                self.content += self.tab + f'yield from mv(xafs_detx, {m["detectorx"]:.3f})\n' 
            
            #########################################
            # move to correct pitch and y positions #
            #########################################
            self.content += self.tab + f'yield from mv(xafs_y, {m["sampley"]:.3f}, xafs_pitch, {m["samplep"]:.3f})\n'

            ####################
            # set Pilatus ROIs #
            ####################
            self.content += self.tab + f'refl.set_rois("roi2", {m["roi2"]})\n'
            self.content += self.tab + f'refl.set_rois("roi3", {m["roi3"]})\n'
            
            ################
            # measure XAFS #
            ################
            command = self.tab + 'yield from xafs(\'%s.ini\'' % self.basename
            for k in m.keys():
                ## skip cells with macro-building parameters that are not INI parameters
                if self.skip_keyword(k):
                    continue
                ## skip element & edge if they are same as default
                elif k in ('element', 'edge'):
                    if m[k] == self.measurements[0][k]:
                        continue
                ## skip cells with only whitespace
                if type(m[k]) is str and len(m[k].strip()) == 0:
                    m[k] = None
                ## if a cell has data, put it in the argument list for xafs()
                if m[k] is not None:
                    if k == 'filename':
                        fname = self.make_filename(m)
                        command += f', filename=\'{fname}\''
                    elif type(m[k]) is int:
                        command += ', %s=%d' % (k, m[k])
                    elif type(m[k]) is float:
                        command += ', %s=%.3f' % (k, m[k])
                    else:
                        command += ', %s=\'%s\'' % (k, m[k])
            command += ', copy=False)\n'
            self.content += command
            self.content += self.tab + 'close_plots()\n\n'


            ########################################
            # approximate time cost of this sample #
            ########################################
            m['mode'] = 'pilatus'  # always pilatus for resonant reflectivity
            self.estimate_time(m, element, edge)
            
        if self.nreps > 1:
            self.tab = ' ' * 8

        if self.close_shutters:
            self.content += self.tab +  'if not dryrun:\n'
            self.content += self.tab +  '    BMMuser.running_macro = False\n'
            self.content += self.tab +  '    BMM_clear_suspenders()\n'
            self.content += self.tab +  '    yield from shb.close_plan()\n'

            


    def get_keywords(self, row, defaultline):
        '''Instructions for parsing spreadsheet columns into keywords.

        arguments
        ---------
        row : contents of a row as read by openpyxl, i.e. ws.rows
        defaultline : True only if this row contains the default
        parameters, i.e. the green row

        This must return a dictionary.  The dictionary keys are the
        keywords related to the column labels from the spreadsheet,
        the values are cell contents, possibly reduced to a specific
        type.

        '''
        this = {'default':    defaultline,
                'measure':    self.truefalse(row[2].value, 'measure'),  # filename and visualization
                'filename':   str(row[3].value),
                'nscans':     row[4].value,
                'start':      row[5].value,
                'element':    row[6].value,      # energy range
                'edge':       row[7].value,
                'focus':      row[8].value,
                'sample':     self.escape_quotes(str(row[9].value)),     # scan metadata
                'prep':       self.escape_quotes(str(row[10].value)),
                'comment':    self.escape_quotes(str(row[11].value)),
                'bounds':     row[12].value,     # scan parameters
                'steps':      row[13].value,
                'times':      row[14].value,
                'detectorx':  row[15].value,
                'flat':       row[16].value,
                'relativep':  row[17].value,
                'samplep':    row[18].value,     # other motors
                'sampley':    row[19].value,
                'spinner':    row[20].value,
                'samplex':    row[21].value,
                'roi2':       re.sub(r'\s+', ' ', re.sub(r',', ' ', str(row[22].value))).split(),
                'roi3':       re.sub(r'\s+', ' ', re.sub(r',', ' ', str(row[23].value))).split(),
                'slitwidth':  row[24].value,
                'slitheight': row[25].value,
                'snapshots':  self.truefalse(row[26].value, 'snapshots' ),  # flags
                'htmlpage':   self.truefalse(row[27].value, 'htmlpage'  ),
                'usbstick':   self.truefalse(row[28].value, 'usbstick'  ),
                'bothways':   self.truefalse(row[29].value, 'bothways'  ),
                'channelcut': self.truefalse(row[30].value, 'channelcut'),
                'ththth':     self.truefalse(row[31].value, 'ththth'    ),
                'url':        row[32].value,
                'doi':        row[33].value,
                'cif':        row[34].value, }
        if this['default'] is True:
            this['mode'] = 'pilatus'  # there is no mode column in the res refl spreadsheet
        return this

