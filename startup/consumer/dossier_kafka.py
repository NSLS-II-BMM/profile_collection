import os, sys, re, socket, ast, datetime, pathlib
from urllib.parse import quote
import numpy, pandas, openpyxl
from scipy.io import savemat
from bluesky import __version__ as bluesky_version


import redis
if not os.environ.get('AZURE_TESTING'):
    redis_host = 'xf06bm-ioc2'
else:
    redis_host = '127.0.0.1'
class NoRedis():
    def set(self, thing, otherthing):
        return None
    def get(self, thing):
        return None
try:
    rkvs = redis.Redis(host=redis_host, port=6379, db=0)
except:
    rkvs = NoRedis()
all_references = ast.literal_eval(rkvs.get('BMM:reference:mapping').decode('UTF8'))

    
from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter

from BMM.periodictable import edge_energy, Z_number, element_symbol, element_name
from tools import echo_slack, experiment_folder
from slack import img_to_slack, post_to_slack

startup_dir = os.path.dirname(__file__)

def log_entry(logger, message):
    #if logger.name == 'BMM file manager logger' or logger.name == 'bluesky_kafka':
    #print(message)
    echo_slack(text = message,
               icon = 'message',
               rid  = None )
    logger.info(message)


class BMMDossier():
    '''A class for generating a static HTML file for documenting an XAS
    measurement at BMM.

    The concept is that most of the metadata needed for the dossier
    will be accumulated in the start document of each scan in the
    sequence.  At the end of the scan sequence, the static HTML file
    will be generated.

    A small number of things are accumulated as objects of the class
    as the scan sequence progresses.  Thus there are some small
    differences between a dossier generated at the time of measurement
    and one made after the fact.

    That static HTML file is made using a set of simple text templates
    which are filled in, then concatenated in a way that suitable for
    the current XAS measurement.

    It is the responsibility of the process sending the kafka messages
    to supply each of the attributes listed below.  All other metadata
    will be found in the start document.

    attributes
    ==========
    folder : str
      target data folder, if None use folder recorded in start doc
      if provided, this is the base folder on central storage for 
      this experiment
    rid : str
      reference ID number for the link to Slack message log capture. 
      This is only relevant during an experiment when Slack messages 
      are being captured in the timeline file.
    uidlist : list of str (or str)
      list of XAFS scan UIDs in the scan sequence
      if a string is provided, it will be converted in a list of length 1
    uid : str
      XAFS scan UID.  If provided this way, it will be appended to 
      self.uidlist

    methods
    =======
    write_dossier
       generate the sample specific dossier file for an XAFS measurement

    raster_dossier
       generate the sample specific dossier file for a raster measurement
    
    sead_dossier
       generate the sample specific dossier file for a SEAD measurement
    
    write_manifest
       update the manifest and the 00INDEX.html file


    instrument state
    ================

    If using one of the automated instruments (sample wheel, Linkam
    stage, LakeShore temperature controller, glancing angle stage,
    motor grid), the class implementing the instrument is responsible
    for supplying a method called dossier_entry.  Here is an example
    from the glancing angle stage class:

           def dossier_entry(self):
              thistext  =  '	    <div>\n'
              thistext +=  '	      <h3>Instrument: Glancing angle stage</h3>\n'
              thistext +=  '	      <ul>\n'
              thistext += f'               <li><b>Spinner:</b> {self.current()}</li>\n'
              thistext += f'               <li><b>Tilt angle:</b> {xafs_pitch.position - self.flat[1]:.1f}</li>\n'      
              thistext += f'               <li><b>Spinning:</b> {"yes" if self.spin else "no"}</li>\n'
              thistext +=  '	      </ul>\n'
              thistext +=  '	    </div>\n'
              return thistext

    This returns a <div> block for the HTML dossier file.  The
    contents of this text include a header3 description of the
    instrument and an unordered list of the most salient aspects of
    the current state of the instrument.

    Admittedly, requiring a method that generates suitable HTML is a
    bit unwieldy, but is allows much flexibility in how the instrument
    gets described in the dossier.

    The dossier_entry methods get used in BMM/xafs.py around line 880.

    The methods raster_dossier and sead_dossier serve this purpose for
    those measurements.

    '''

    instrument = None
    rid = None
    uidlist = []

    def set_parameters(self, **kwargs):
        '''Set dossier parameters from strings in the Kafka message.

        Take care with "uid" / "uidlist" to be sure that strings are
        turned into lists of strings.  All dossier methods expect that
        self.uidlist is a list of strings, even if it is a list of one.

        '''
        for k in kwargs.keys():
            if k == 'dossier':
                continue
            elif k == 'uid':
                self.uidlist.append(kwargs['uid'])
            elif k == 'uidlist' and type(kwargs['uidlist']) is str:
                self.uidlist = [kwargs['uidlist'],]
            else:
                setattr(self, k, kwargs[k])


    def write_dossier(self, bmm_catalog, logger):
        '''
        Write a dossier for an XAFS scan sequence.
        '''

        if len(self.uidlist) == 0:
            log_entry(logger, '*** cannot write dossier, uidlist is empty')
            return None

        ## gather information for the dossier from the start document
        ## of the first scan in the sequence
        startdoc = bmm_catalog[self.uidlist[0]].metadata['start']
        XDI = startdoc['XDI']
        if '_snapshots' in XDI:
            snapshots = XDI['_snapshots']
        else:
            snapshots = {}
        

        folder = self.folder
        if folder is None or folder == '':
            folder = XDI["_user"]["folder"]
        ## determine folder from content of start doc.
        ## What about past scans?
        folder = experiment_folder(bmm_catalog, self.uidlist[0])
        self.folder = folder
            
        ## test if XAS data file can be found
        if XDI['_user']['filename'] is None or XDI["_user"]["start"] is None:
            log_entry(logger, '*** Filename and/or start number not given.  (xafs_dossier).')
            return None
        firstfile = f'{XDI["_user"]["filename"]}.{XDI["_user"]["start"]:03d}'
        if not os.path.isfile(os.path.join(folder, firstfile)):
            log_entry(logger, f'*** Could not find {os.path.join(folder, firstfile)}')
            return None

        ## determine names of output dossier files
        basename     = XDI['_user']['filename']
        htmlfilename = os.path.join(folder, 'dossier/', XDI['_user']['filename']+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))):
                seqnumber += 1
            basename     = "%s-%2.2d" % (XDI['_user']['filename'],seqnumber)
            htmlfilename = os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))

        ## sanity check the "report ID" (used to link to correct position in messagelog.html
        if self.rid is None: self.rid=''

        try:
            # dossier header
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_top.tmpl')) as f:
                content = f.readlines()
            thiscontent = ''.join(content).format(measurement   = 'XAFS',
                                                  filename      = XDI['_user']['filename'],
                                                  date          = XDI['_user']['startdate'],
                                                  rid           = self.rid,
                                                  seqnumber     = seqnumber, )

            # left sidebar, entry for XRF file in the case of fluorescence data
            thismode = self.plotting_mode(XDI['_user']['mode'])
            if thismode == 'xs' or thismode == 'xs1':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(basename      = basename,
                                                       xrffile       = quote('../XRF/'+XDI['_xrffile']),
                                                       xrfuid        = snapshots['xrf_uid'], )

            # middle part of dossier
            instrument = XDI['_user']['instrument']
            if instrument is None or instrument == '':
                instrument = self.instrument_default()
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_middle.tmpl')) as f:
                content = f.readlines()
            thiscontent += ''.join(content).format(basename      = basename,
                                                   scanlist      = self.generate_scanlist(bmm_catalog),  # uses self.uidlist
                                                   motors        = self.motor_sidebar(bmm_catalog),
                                                   sample        = XDI['Sample']['name'],
                                                   prep          = XDI['Sample']['prep'],
                                                   comment       = XDI['_user']['comment'],
                                                   instrument    = instrument,)
            

            # middle part, cameras, one at a time and only if actually snapped
            if 'webcam_uid' in snapshots and snapshots['webcam_uid'] != '':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+snapshots['webcam_file']),
                                                       uid         = snapshots['webcam_uid'],
                                                       camera      = 'webcam',
                                                       description = 'XAS web camera', )
            if 'anacam_uid' in snapshots and snapshots['anacam_uid'] != '':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+snapshots['analog_file']),
                                                       uid         = snapshots['anacam_uid'],
                                                       camera      = 'anacam',
                                                       description = 'analog pinhole camera', )
            if 'usbcam1_uid' in snapshots and snapshots['usbcam1_uid'] != '':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+snapshots['usb1_file']),
                                                       uid         = snapshots['usbcam1_uid'],
                                                       camera      = 'usbcam1',
                                                       description = 'USB camera #1', )
            if 'usbcam2_uid' in snapshots and snapshots['usbcam2_uid'] != '':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+snapshots['usb2_file']),
                                                       uid         = snapshots['usbcam2_uid'],
                                                       camera      = 'usb2cam',
                                                       description = 'USB camera #2', )
            
            # middle part, XRF and glancing angle alignment images
            if thismode == 'xs' or thismode == 'xs1':
                el = XDI['Element']['symbol']
                if '4-element SDD' in bmm_catalog[self.uidlist[0]].metadata['start']['detectors']:
                    rois = [int(bmm_catalog[snapshots['xrf_uid']].primary.data[el+'1'][0]),
                            int(bmm_catalog[snapshots['xrf_uid']].primary.data[el+'2'][0]),
                            int(bmm_catalog[snapshots['xrf_uid']].primary.data[el+'3'][0]),
                            int(bmm_catalog[snapshots['xrf_uid']].primary.data[el+'4'][0])]
                    ocrs = [int(numpy.array(bmm_catalog[snapshots['xrf_uid']].primary.data['4-element SDD_channel01_xrf']).sum()),
                            int(numpy.array(bmm_catalog[snapshots['xrf_uid']].primary.data['4-element SDD_channel02_xrf']).sum()),
                            int(numpy.array(bmm_catalog[snapshots['xrf_uid']].primary.data['4-element SDD_channel03_xrf']).sum()),
                            int(numpy.array(bmm_catalog[snapshots['xrf_uid']].primary.data['4-element SDD_channel04_xrf']).sum()) ]
                elif '1-element SDD' in bmm_catalog[self.uidlist[0]].metadata['start']['detectors']:
                    rois = [int(bmm_catalog[snapshots['xrf_uid']].primary.data[el+'8'][0]),]
                    ocrs = [int(numpy.array(bmm_catalog[snapshots['xrf_uid']].primary.data['1-element SDD_channel08_xrf']).sum()),]
                elif '7-element SDD' in bmm_catalog[self.uidlist[0]].metadata['start']['detectors']:
                    pass

                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_image.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(xrfsnap   = quote('../XRF/'+snapshots['xrf_image']),
                                                       pccenergy = '%.1f' % XDI['_user']['pccenergy'],
                                                       ocrs      = ', '.join(map(str,ocrs)),
                                                       rois      = ', '.join(map(str,rois)),
                                                       symbol    = XDI['Element']['symbol'],)
                if 'ga_filename' in snapshots:
                    with open(os.path.join(startup_dir, 'tmpl', 'dossier_ga.tmpl')) as f:
                        content = f.readlines()
                    thiscontent += ''.join(content).format(ga_align = quote('../snapshots/'+ snapshots['ga_filename']),
                                                           ga_yuid  = snapshots['ga_yuid'],
                                                           ga_puid  = snapshots['ga_pitchuid'],
                                                           ga_fuid  = snapshots['ga_fuid'], )

            # end of dossier
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_bottom.tmpl')) as f:
                content = f.readlines()
            this_ref = all_references[XDI['Element']['symbol']][3]

            thiscontent += ''.join(content).format(e0            = '%.1f' % edge_energy(XDI['Element']['symbol'], XDI['Element']['edge']),
                                                   edge          = XDI['Element']['edge'],
                                                   element       = self.element_text(XDI['Element']['symbol']),
                                                   mode          = XDI['_user']['mode'],
                                                   bounds        = ", ".join(map(str, XDI['_user']['bounds_given'])),
                                                   steps         = XDI['_user']['steps'],
                                                   times         = XDI['_user']['times'],
                                                   reference     = re.sub(r'(\d+)', r'<sub>\1</sub>', this_ref),
                                                   seqstart      = datetime.datetime.fromtimestamp(bmm_catalog[self.uidlist[0]].metadata['start']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                                   seqend        = datetime.datetime.fromtimestamp(bmm_catalog[self.uidlist[-1]].metadata['stop']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                                   mono          = self.mono_text(bmm_catalog),
                                                   pdsmode       = '%s  (%s)' % self.pdstext(bmm_catalog),
                                                   pccenergy     = '%.1f' % XDI['_user']['pccenergy'],
                                                   experimenters = XDI['Scan']['experimenters'],
                                                   gup           = XDI['Facility']['GUP'],
                                                   saf           = XDI['Facility']['SAF'],
                                                   url           = XDI['_user']['url'],
                                                   doi           = XDI['_user']['doi'],
                                                   cif           = XDI['_user']['cif'],
                                                   initext       = highlight(XDI['_user']['initext'], IniLexer(),    HtmlFormatter()),
                                                   clargs        = highlight(XDI['_user']['clargs'],  PythonLexer(), HtmlFormatter()),
                                                   filename      = XDI['_user']['filename'],)

            with open(htmlfilename, 'a') as o:
                o.write(thiscontent)

            log_entry(logger, f'wrote XAFS dossier: {htmlfilename}')
        except Exception as E:
            log_entry(logger, f'failed to write dossier file {htmlfilename}\n' + str(E))


        self.manifest_file = os.path.join(folder, 'dossier', 'MANIFEST')            
        manifest = open(self.manifest_file, 'a')
        manifest.write(f'xafs␣{htmlfilename}\n')
        manifest.close()
        self.write_manifest(scantype='XAFS', startdate=XDI['_user']['startdate'])


    def write_manifest(self, scantype='XAFS', startdate=''):
        '''Update the scan manifest and the corresponding static html file.'''
        with open(self.manifest_file) as f:
            lines = [line.rstrip('\n') for line in f]

        experimentlist = ''
        for l in lines:
            (scantype, fname) = l.split('␣')
            if not os.path.isfile(fname):
                continue
            this = os.path.basename(fname)
            experimentlist += f'<li>{scantype}: <a href="./{this}">{this}</a></li>\n'

        with open(os.path.join(startup_dir, 'tmpl', 'manifest.tmpl')) as f:
            content = f.readlines()
        indexfile = os.path.join(self.folder, 'dossier', '00INDEX.html')
        o = open(indexfile, 'w')
        o.write(''.join(content).format(date           = startdate,
                                        experimentlist = experimentlist,))
        o.close()



    def plotting_mode(self, mode):
        '''Return a sane string to describe the plotting mode.'''
        mode = mode.lower()
        if mode == 'xs1':
            return 'xs1'
        elif any(x in mode for x in ('xs', 'fluo', 'flou', 'both')):
            return 'xs'
        #elif any(x in mode for x in ('fluo', 'flou', 'both')):
        #    return 'fluo'  # deprecated analog fluo detection
        elif mode == 'ref':
            return 'ref'
        elif mode == 'yield':
            return 'yield'
        elif mode == 'test':
            return 'test'
        elif mode == 'icit':
            return 'icit'
        elif mode == 'ici0':
            return 'ici0'
        else:
            return 'trans'

    def element_text(self, element='Po'):
        '''Return a string describing the element.  Returns Po if not
        specified or not specified correctly.'''
        if Z_number(element) is None:
            return ''
        else:
            thistext  = f'{element} '
            thistext += f'(<a href="https://en.wikipedia.org/wiki/{element_name(element)}">'
            thistext += f'{element_name(element)}</a>, '
            thistext += f'Z={Z_number(element)})'
            return thistext
        
    def generate_scanlist(self, bmm_catalog):
        '''Generate the html text for the XAS scan side bar for the XAFS
        dossier from the uidlist.'''
        template = '''
<li>
  <a href="../{filename}.{ext:03d}"
     title="Click to see the text of {filename}.{ext:03d}">
         {printedname}.{ext:03d}
  </a>
  <br>&nbsp;&nbsp;
  <a href="javascript:void(0)"
     onclick="toggle_visibility(\'{filename}.{ext:03d}\');"
     title="This is the scan number for {filename}.{ext:03d}, click to show/hide its UID">
         #{scanid}
  </a>
  <div id="{filename}.{ext:03d}" style="display:none;"><small>{uid}</small></div>
  <br>&nbsp;&nbsp;'''
        hdf5template = '''<a href="javascript:void(0)"
     onclick="toggle_visibility(\'{filename}.{ext:03d}.h5\');"
     title="This is HDF5 file associated with {filename}.{ext:03d}, click to show/hide the HDF5 filename">
         HDF5
  </a>
  <div id="{filename}.{ext:03d}.h5" style="display:none;"><small>{hdf5file}</small></div>
</li>\n
'''
        
#        template = '<li><a href="../{filename}.{ext:03d}" title="Click to see the text of {filename}.{ext:03d}">{printedname}.{ext:03d}</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="javascript:void(0)" onclick="toggle_visibility(\'{filename}.{ext:03d}\');" title="This is the scan number for {filename}.{ext:03d}, click to show/hide its UID">#{scanid}</a><div id="{filename}.{ext:03d}" style="display:none;"><small>{uid}</small></div></li>\n'

        text = ''
        for u in self.uidlist:
            filename = bmm_catalog[self.uidlist[0]].metadata['start']['XDI']['_user']['filename']
            ext = bmm_catalog[self.uidlist[0]].metadata['start']['XDI']['_user']['start']
            printedname = filename
            hdf5file = self.hdf5_filename(bmm_catalog, u)
            if len(filename) > 11:
                printedname = filename[0:6] + '&middot;&middot;&middot;' + filename[-5:]
            text += template.format(filename    = filename,
                                    printedname = printedname,
                                    ext         = ext,
                                    scanid      = bmm_catalog[u].metadata['start']['scan_id'],
                                    uid         = u,)
            if hdf5file is not None:
                text += hdf5template.format(filename    = filename,
                                            ext         = ext,
                                            hdf5file    = hdf5file,)
            ext = ext + 1
        return text

    def mono_text(self, bmm_catalog):
        '''Text explaining the monochromator used for the measurement.  This
        is computed from motor values in the baseline.'''
        dcmx = bmm_catalog[self.uidlist[0]].baseline.data['dcm_x'][0]
        if dcmx > 10:
            return 'Si(311)'
        elif bmm_catalog[self.uidlist[0]].metadata['start']['XDI']['_user']['ththth'] is True:
            return 'Si(333)'
        else:
            return 'Si(111)'


    def pdstext(self, bmm_catalog):
        '''Text explaining the photon delivery mode used for the measurement.
        This is computed from motor values in the baseline.'''
        m2v = bmm_catalog[self.uidlist[0]].baseline.data['m2_vertical'][0]
        m2p = bmm_catalog[self.uidlist[0]].baseline.data['m2_pitch'][0]
        m3p = bmm_catalog[self.uidlist[0]].baseline.data['m3_pitch'][0]
        m3v = bmm_catalog[self.uidlist[0]].baseline.data['m3_vertical'][0]
        m3l = bmm_catalog[self.uidlist[0]].baseline.data['m3_lateral'][0]
        if m2v < 0: # this is a focused mode
            if m2p > 3:
                return ('XRD', 'focused at goniometer, >8 keV')
            else:
                if m3v > -2:
                    return ('A', 'focused, >8 keV')
                elif m3v > -7:
                    return ('B', 'focused, <6 keV')
                else:
                    return ('C', 'focused, 6 to 8 keV')
        else:
            if m3p < 3:
                return ('F', 'unfocused, <6 keV')
            elif m3l > 0:
                return ('D', 'unfocused, >8 keV')
            else:
                return ('E', 'unfocused, 6 to 8 keV')


            
        

    def wheel_slot(self, value):
        '''Return the current slot number for a sample wheel computed from the
        xafs_wheel motor position.'''
        slotone = -30
        angle = round(value)
        this = round((-1*slotone-15+angle) / (-15)) % 24
        if this == 0: this = 24
        return this

    def spinner(self, pos):
        '''Return the current spinner number as an integer computed as the
        xafs_garot motor position.'''
        cur = pos % 360
        here = (9-round(cur/45)) % 8
        if here == 0:
            here = 8
        return here


    def hdf5_filename(self, bmm_catalog, uid):
        '''Find the path/name of the asset file associated with UID
        '''
        for d in bmm_catalog[uid].documents():
            if d[0] == 'resource':
                this = os.path.join(d[1]['root'], d[1]['resource_path'])
                if '_%d' in this:
                    this = this % 0
                return(this)
        return None
    
    
    def motor_sidebar(self, bmm_catalog):
        baseline = bmm_catalog[self.uidlist[0]].baseline.read()

        '''Generate a list of motor positions for the sidebar of the static
        html page for a scan sequence.  Return value is a long string
        with html tags and entities embedded in the string.

        All motor positions are taken from the first entry in the
        record's baseline stream.

        Parameters
        ----------
        bmm_catalog : Tiled catalog
            catalog in which to find the record for a UID string

        >>> text = dossier.motor_sidebar(bmm_catalog)

        '''
        motors = ''

        motors +=  '<span class="motorheading">XAFS stages:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>xafs_x, {baseline["xafs_x"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_y, {baseline["xafs_y"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_pitch, {baseline["xafs_pitch"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_roll, {baseline["xafs_roll"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_wheel, {baseline["xafs_wheel"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_ref, {baseline["xafs_ref"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_refx, {baseline["xafs_refx"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_refy, {baseline["xafs_refy"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_det, {baseline["xafs_det"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_garot, {baseline["xafs_garot"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        motors +=  '            <span class="motorheading">Instruments:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>slot, {self.wheel_slot(float(baseline["xafs_wheel"][0]))}</div>\n'
        motors += f'              <div>spinner, {self.spinner(float(baseline["xafs_garot"][0]))}</div>\n'
        motors += f'              <div>dm3_bct, {baseline["dm3_bct"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        motors +=  '            <span class="motorheading">Slits3:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>slits3_vsize, {baseline["slits3_vsize"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_vcenter, {baseline["slits3_vcenter"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_hsize, {baseline["slits3_hsize"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_hcenter, {baseline["slits3_hcenter"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_top, {baseline["slits3_top"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_bottom, {baseline["slits3_bottom"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_inboard, {baseline["slits3_inboard"][0]:.3f}</div>\n'
        motors += f'              <div>slits3_outboard, {baseline["slits3_outboard"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        motors +=  '            <span class="motorheading">M2:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>m2_vertical, {baseline["m2_vertical"][0]:.3f}</div>\n'
        motors += f'              <div>m2_lateral, {baseline["m2_lateral"][0]:.3f}</div>\n'
        motors += f'              <div>m2_pitch, {baseline["m2_pitch"][0]:.3f}</div>\n'
        motors += f'              <div>m2_roll, {baseline["m2_roll"][0]:.3f}</div>\n'
        motors += f'              <div>m2_yaw, {baseline["m2_yaw"][0]:.3f}</div>\n'
        motors += f'              <div>m2_yu, {baseline["m2_yu"][0]:.3f}</div>\n'
        motors += f'              <div>m2_ydo, {baseline["m2_ydo"][0]:.3f}</div>\n'
        motors += f'              <div>m2_ydi, {baseline["m2_ydi"][0]:.3f}</div>\n'
        motors += f'              <div>m2_xu, {baseline["m2_xu"][0]:.3f}</div>\n'
        motors += f'              <div>m2_xd, {baseline["m2_xd"][0]:.3f}</div>\n'
        motors += f'              <div>m2_bender, {baseline["m2_bender"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        stripe = '(Rh/Pt stripe)'
        if baseline['m3_xu'][0] < 0:
            stripe = '(Si stripe)'
        motors += f'            <span class="motorheading">M3 {stripe}:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>m3_vertical, {baseline["m3_vertical"][0]:.3f}</div>\n'
        motors += f'              <div>m3_lateral, {baseline["m3_lateral"][0]:.3f}</div>\n'
        motors += f'              <div>m3_pitch, {baseline["m3_pitch"][0]:.3f}</div>\n'
        motors += f'              <div>m3_roll, {baseline["m3_roll"][0]:.3f}</div>\n'
        motors += f'              <div>m3_yaw, {baseline["m3_yaw"][0]:.3f}</div>\n'
        motors += f'              <div>m3_yu, {baseline["m3_yu"][0]:.3f}</div>\n'
        motors += f'              <div>m3_ydo, {baseline["m3_ydo"][0]:.3f}</div>\n'
        motors += f'              <div>m3_ydi, {baseline["m3_ydi"][0]:.3f}</div>\n'
        motors += f'              <div>m3_xu, {baseline["m3_xu"][0]:.3f}</div>\n'
        motors += f'              <div>m3_xd, {baseline["m3_xd"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        motors +=  '            <span class="motorheading">XAFS table:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>xt_vertical, {baseline["xafs_table_vertical"][0]:.3f}</div>\n'
        motors += f'              <div>xt_pitch, {baseline["xafs_table_pitch"][0]:.3f}</div>\n'
        motors += f'              <div>xt_roll, {baseline["xafs_table_roll"][0]:.3f}</div>\n'
        motors += f'              <div>xt_yu, {baseline["xafs_table_yu"][0]:.3f}</div>\n'
        motors += f'              <div>xt_ydo, {baseline["xafs_table_ydo"][0]:.3f}</div>\n'
        motors += f'              <div>xt_ydi, {baseline["xafs_table_ydi"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'


        motors +=  '            <span class="motorheading">Slits2:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>slits2_vsize, {baseline["slits2_vsize"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_vcenter, {baseline["slits2_vcenter"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_hsize, {baseline["slits2_hsize"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_hcenter, {baseline["slits2_hcenter"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_top, {baseline["slits2_top"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_bottom, {baseline["slits2_bottom"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_inboard, {baseline["slits2_inboard"][0]:.3f}</div>\n'
        motors += f'              <div>slits2_outboard, {baseline["slits2_outboard"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'

        motors +=  '            <span class="motorheading">Diagnostics:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>dm3_foils, {baseline["dm3_foils"][0]:.3f}</div>\n'
        motors += f'              <div>dm2_fs, {baseline["dm2_fs"][0]:.3f}</div>\n'
        motors +=  '            </div>\n'
        
        return motors
    
    def instrument_default(self):
        thistext  =  '''
	    <div>
	      <h3>Instrument</h3>
	      <ul>
               <li>(no instrument information)</li>
	      </ul>
	    </div>
'''
        return thistext



    def sead_instrument_entry(self, seadimage, seaduid):
        thistext  =  '      <div>\n'
        thistext +=  '        <h3>Instrument: SEAD scan</h3>\n'
        thistext += f'          <a href="../snapshots/{seadimage}">\n'
        thistext += f'                        <img src="../snapshots/{seadimage}" width="300" alt="" /></a>\n'
        thistext +=  '          <br>'
        thistext += f'          <a href="javascript:void(0)" onclick="toggle_visibility(\'areascan\');" title="Click to show/hide the UID of this areascan">(uid)</a><div id="areascan" style="display:none;"><small>{seaduid}</small></div>\n'
        thistext +=  '      </div>\n'
        return thistext

    
    def sead_dossier(self, catalog, logger):
        '''Write a dossier for a SEAD measurement. '''

        if len(self.uidlist) == 0:
            log_entry(logger, '*** cannot write SEAD dossier, uidlist is empty')
            return None

        ## gather information for the dossier from the start document
        ## of the first scan in the sequence
        startdoc = catalog[self.uidlist[0]].metadata['start']
        XDI = startdoc['XDI']
        if '_snapshots' in XDI:
            snapshots = XDI['_snapshots']
        else:
            snapshots = {}
        

        folder = self.folder
        if folder is None or folder == '':
            folder = XDI["_user"]["folder"]
        ## determine folder from content of start doc.
        ## What about past scans?
        folder = experiment_folder(catalog, self.uidlist[0])
        self.folder = folder
            
        ## test if SEAD data file can be found
        if XDI['_user']['filename'] is None or XDI["_user"]["start"] is None:
            log_entry(logger, '*** Filename and/or start number not given.  (sead_dossier).')
            return None
        firstfile = f'{XDI["_user"]["filename"]}.{XDI["_user"]["start"]:03d}'
        if not os.path.isfile(os.path.join(folder, firstfile)):
            log_entry(logger, f'*** Could not find {os.path.join(folder, firstfile)}')
            return None


        ## determine names of output dossier files
        basename     = XDI['_user']['filename']
        htmlfilename = os.path.join(folder, 'dossier/', XDI['_user']['filename']+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))):
                seqnumber += 1
            basename     = "%s-%2.2d" % (XDI['_user']['filename'],seqnumber)
            htmlfilename = os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))


        with open(os.path.join(startup_dir, 'tmpl', 'sead_dossier.tmpl')) as f:
                content = f.readlines()
        thiscontent = ''.join(content).format(measurement   = 'SEAD',
                                              filename      = XDI['_user']['filename'],
                                              sead          = os.path.basename(XDI['_filename']),
                                              date          = XDI['_user']['startdate'],
                                              seqnumber     = seqnumber,  # need to replicate from above
                                              rid           = self.rid,
                                              energy        = f'{XDI["Scan"]["edge_energy"]:1f}',
                                              edge          = f'{XDI["Element"]["edge"]}',
                                              element       = self.element_text(XDI['Element']['symbol']),
                                              sample        = XDI['Sample']['name'],
                                              prep          = XDI['Sample']['prep'],
                                              comment       = XDI['_user']['comment'],
                                              instrument    = self.sead_instrument_entry(XDI['_user']['pngfile'], self.uidlist[0]),
                                              npoints       = len(catalog[self.uidlist[0]].primary.data["time"]),
                                              dwell         = XDI['Scan']['dwell_time'],
                                              delay         = XDI['Scan']['delay'],
                                              shutter       = XDI['_user']['shutter'],
                                              websnap       = quote('../snapshots/'+snapshots['webcam_file']),
                                              webuid        = snapshots['webcam_uid'],
                                              anasnap       = quote('../snapshots/'+snapshots['analog_file']),
                                              anauid        = snapshots['anacam_uid'],
                                              usb1snap      = quote('../snapshots/'+snapshots['usb1_file']),
                                              usb1uid       = snapshots['usbcam1_uid'],
                                              usb2snap      = quote('../snapshots/'+snapshots['usb2_file']),
                                              usb2uid       = snapshots['usbcam2_uid'],
                                              mode          = XDI['_user']['mode'],
                                              motors        = self.motor_sidebar(catalog),
                                              seqstart      = datetime.datetime.fromtimestamp(catalog[self.uidlist[0]].metadata['start']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                              seqend        = datetime.datetime.fromtimestamp(catalog[self.uidlist[-1]].metadata['stop']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                              mono          = self.mono_text(catalog),
                                              pdsmode       = '%s  (%s)' % self.pdstext(catalog),
                                              experimenters = XDI['_user']['experimenters'],
                                              gup           = XDI['Facility']['GUP'],
                                              saf           = XDI['Facility']['SAF'],
                                              url           = XDI['_user']['url'],
                                              doi           = XDI['_user']['doi'],
                                              cif           = XDI['_user']['cif'],
                                              initext       = highlight(XDI['_user']['initext'], IniLexer(), HtmlFormatter()),
                                              clargs        = highlight(XDI['_user']['clargs'], PythonLexer(), HtmlFormatter()),
                                              hdf5file      = self.hdf5_filename(catalog, self.uidlist[0]),
        )
        with open(htmlfilename, 'a') as o:
            o.write(thiscontent)

        log_entry(logger, f'wrote SEAD dossier: {htmlfilename}')

        self.manifest_file = os.path.join(folder, 'dossier', 'MANIFEST')            
        manifest = open(self.manifest_file, 'a')
        manifest.write(f'sead␣{htmlfilename}\n')
        manifest.close()
        self.write_manifest(scantype='SEAD', startdate=XDI['_user']['startdate'])





    def raster_instrument_entry(self, rasterimage, rasteruid):
        thistext  =  '      <div>\n'
        thistext +=  '        <h3>Instrument: Raster scan</h3>\n'
        thistext += f'          <a href="../maps/{rasterimage}">\n'
        thistext += f'                        <img src="../maps/{rasterimage}" width="300" alt="" /></a>\n'
        thistext +=  '          <br>'
        thistext += f'          <a href="javascript:void(0)" onclick="toggle_visibility(\'areascan\');" title="Click to show/hide the UID of this areascan">(uid)</a><div id="areascan" style="display:none;"><small>{rasteruid}</small></div>\n'
        thistext +=  '      </div>\n'
        return thistext

    def raster_dossier(self, catalog, logger):
        '''Write a dossier for a raster measurement. '''

        if len(self.uidlist) == 0:
            log_entry(logger, '*** cannot write dossier, uidlist is empty')
            return None

        ## gather information for the dossier from the start document
        ## of the first scan in the sequence
        startdoc = catalog[self.uidlist[0]].metadata['start']
        XDI = startdoc['XDI']
        if '_snapshots' in XDI:
            snapshots = XDI['_snapshots']
        else:
            snapshots = {}


        folder = self.folder
        if folder is None or folder == '':
            folder = XDI["_user"]["folder"]
        ## determine folder from content of start doc.
        ## What about past scans?
        folder = experiment_folder(bmm_catalog, self.uidlist[0])
        self.folder = folder
            

        ## check for filename stub
        if XDI['_user']['filename'] is None:
            log_entry(logger, '*** Filename not given.  (raster_dossier).')
            return None


        ## determine names of output dossier files
        basename     = XDI['_user']['filename']
        htmlfilename = os.path.join(folder, 'dossier/', XDI['_user']['filename']+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))):
                seqnumber += 1
            basename     = "%s-%2.2d" % (XDI['_user']['filename'],seqnumber)
            htmlfilename = os.path.join(folder, 'dossier', "%s-%2.2d.html" % (XDI['_user']['filename'],seqnumber))

        with open(os.path.join(startup_dir, 'tmpl', 'raster_dossier.tmpl')) as f:
                content = f.readlines()
        thiscontent = ''.join(content).format(measurement   = 'RASTER',
                                              filename      = XDI['_user']['filename'],
                                              basename      = basename,
                                              date          = XDI['_user']['startdate'],
                                              seqnumber     = seqnumber,
                                              rid           = self.rid,
                                              energy        = f'{XDI["Beamline"]["energy"]:1f}',
                                              edge          = f'{XDI["Element"]["edge"]}',
                                              element       = self.element_text(XDI['Element']['symbol']),
                                              sample        = XDI['Sample']['name'],
                                              prep          = XDI['Sample']['prep'],
                                              comment       = XDI['_user']['comment'],
                                              instrument    = self.raster_instrument_entry(XDI['_snapshots']['pngout'], self.uidlist[0]),
                                              fast_motor    = XDI['_user']['fast_motor'],
                                              slow_motor    = XDI['_user']['slow_motor'],
                                              fast_init     = XDI['_user']['fast_init'],
                                              slow_init     = XDI['_user']['slow_init'],
                                              websnap       = quote('../snapshots/'+snapshots['webcam_file']),
                                              webuid        = snapshots['webcam_uid'],
                                              anasnap       = quote('../snapshots/'+snapshots['analog_file']),
                                              anauid        = snapshots['anacam_uid'],
                                              usb1snap      = quote('../snapshots/'+snapshots['usb1_file']),
                                              usb1uid       = snapshots['usbcam1_uid'],
                                              usb2snap      = quote('../snapshots/'+snapshots['usb2_file']),
                                              usb2uid       = snapshots['usbcam2_uid'],
                                              xlsxout       = XDI['_snapshots']['xlsxout'],
                                              matout        = XDI['_snapshots']['matout'],
                                              mode          = XDI['_user']['mode'],
                                              motors        = self.motor_sidebar(catalog),
                                              seqstart      = datetime.datetime.fromtimestamp(catalog[self.uidlist[0]].metadata['start']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                              seqend        = datetime.datetime.fromtimestamp(catalog[self.uidlist[-1]].metadata['stop']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                              mono          = self.mono_text(catalog),
                                              pdsmode       = '%s  (%s)' % self.pdstext(catalog),
                                              experimenters = XDI['_user']['experimenters'],
                                              gup           = XDI['Facility']['GUP'],
                                              saf           = XDI['Facility']['SAF'],
                                              url           = XDI['_user']['url'],
                                              doi           = XDI['_user']['doi'],
                                              cif           = XDI['_user']['cif'],
                                              initext       = highlight(XDI['_user']['initext'], IniLexer(), HtmlFormatter()),
                                              clargs        = highlight(XDI['_user']['clargs'], PythonLexer(), HtmlFormatter()),
                                              hdf5file      = self.hdf5_filename(catalog, self.uidlist[0]),
        )
        with open(htmlfilename, 'a') as o:
            o.write(thiscontent)

        log_entry(logger, f'wrote raster dossier: {htmlfilename}')

        self.manifest_file = os.path.join(folder, 'dossier', 'MANIFEST')            
        manifest = open(self.manifest_file, 'a')
        manifest.write(f'raster␣{htmlfilename}\n')
        manifest.close()
        self.write_manifest()


        

class XASFile():

    def plot_hint(self, catalog=None, uid=None):
        text = 'ln(I0/It)  --  ln($5/$6)'
        el = catalog[uid].metadata['start']['XDI']['Element']['symbol']
        
        if '1-element SDD' in catalog[uid].metadata['start']['detectors']:
            text = f'{el}8/I0  --  $8/$5'
        elif '4-element SDD' in catalog[uid].metadata['start']['detectors']:
            text = f'({el}1+{el}2+{el}3+{el}4)/I0  --  ($8+$9+$10+$11)/$5'
        elif '7-element SDD' in catalog[uid].metadata['start']['detectors']:
            text = f'({el}1+{el}2+{el}3+{el}4+{el}5+{el}6+{el}7)/I0  --  ($8+$9+$10+$11+$12+$13+$14)/$5'
        elif 'reference' in catalog[uid].metadata['start']['plan_name']:
            text = 'ln(It/Ir)  --  ln($6/$7)'
        elif 'yield' in catalog[uid].metadata['start']['plan_name']:
            text = 'ln(It/Ir)  --  ln($8/$5)'
        elif 'test' in catalog[uid].metadata['start']['plan_name']:
            text = 'I0  --  $5'
        return text
    
    def to_xdi(self, catalog=None, uid=None, filename=None, logger=None):
        '''Write an XDI-style file for an XAS scan.

        '''
        
        xdi = catalog[uid].metadata["start"]["XDI"]
        fname = os.path.join(experiment_folder(catalog, uid), filename)
        handle = open(fname, 'w')
        handle.write(f'# XDI/1.0 BlueSky/{bluesky_version} BMM/{pathlib.Path(sys.executable).parts[-3]}\n')

        ## header lines with metadata from the XDi dictionary
        for family in ('Beamline', 'Detector', 'Element', 'Facility', 'Mono', 'Sample', 'Scan'):
            for k in xdi[family].keys():
                if family == 'Sample' and k == 'comment':
                    continue
                if family == 'Sample' and k == 'extra_metadata':
                    continue
                handle.write(f'# {family}.{k}: {xdi[family][k]}\n')
        start = datetime.datetime.fromtimestamp(catalog[uid].metadata['start']['time']).strftime("%Y-%m-%dT%H:%M:%S") # '%A, %d %B, %Y %I:%M %p')
        end   = datetime.datetime.fromtimestamp(catalog[uid].metadata['stop']['time']).strftime("%Y-%m-%dT%H:%M:%S") # '%A, %d %B, %Y %I:%M %p')
        handle.write(f'# Scan.start_time: {start}\n')
        handle.write(f'# Scan.end_time: {end}\n')
        handle.write(f'# Scan.uid: {uid}\n')
        handle.write(f'# Scan.transient_id: {catalog[uid].metadata["start"]["scan_id"]}\n')
        handle.write(f'# Scan.plot_hint: {self.plot_hint(catalog=catalog, uid=uid)}\n')
        handle.write( '# Column.1: energy eV\n')
        handle.write( '# Column.2: requested_energy eV\n')
        handle.write( '# Column.3: measurement_time seconds\n')
        handle.write( '# Column.4: xmu\n')
        handle.write( '# Column.5: I0 nA\n')
        handle.write( '# Column.6: It nA\n')
        handle.write( '# Column.7: Ir nA\n')

        ## Column.N header lines
        column_list = ['dcm_energy', 'dcm_energy_setpoint', 'dwti_dwell_time', 'I0', 'It', 'Ir']
        column_labels = ['energy', 'requested_energy', 'measurement_time', 'xmu', 'I0', 'It', 'Ir']
        
        el = catalog[uid].metadata['start']['XDI']['Element']['symbol']
        nchan = 0
        if '1-element SDD' in catalog[uid].metadata['start']['detectors']:
            nchan = 1
            column_list.append(f'{el}8')
            column_labels.append(f'{el}8')
            handle.write(f'# Column.8: {el}8\n')
        elif '4-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            nchan = 4
        elif '7-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            nchan = 7
        if nchan > 0:
            for i in range(1, nchan+1):
                handle.write(f'# Column.{i+7}: {el}{i}\n')

        ## prepare data table and insert xmu column
        xa = catalog[uid].primary.read(column_list)
        p = xa.to_pandas()
        column_list.insert(3, 'xmu')
        if '1-element SDD' in catalog[uid].metadata['start']['detectors']:
            p['xmu'] = p[f'{el}8']/p['I0']
        elif '4-element SDD' in catalog[uid].metadata['start']['detectors']:
            p['xmu'] = (p[f'{el}1']+p[f'{el}2']+p[f'{el}3']+p[f'{el}4'])/p['I0']
        elif '7-element SDD' in catalog[uid].metadata['start']['detectors']:
            p['xmu'] = (p[f'{el}1']+p[f'{el}2']+p[f'{el}3']+p[f'{el}4']+p[f'{el}5']+p[f'{el}6']+p[f'{el}7'])/p['I0']
        elif 'transmission' in catalog[uid].metadata['start']['plan_name']:
            p['xmu'] = numpy.log(p['It']/p['I0'])
        elif 'reference' in catalog[uid].metadata['start']['plan_name']:
            p['xmu'] = numpy.log(p['Ir']/p['It'])
        elif 'yield' in catalog[uid].metadata['start']['plan_name']:
            p['xmu'] = p['Iy']/p['It']
        elif 'test' in catalog[uid].metadata['start']['plan_name']:
            p['xmu'] = p['I0']
        else:
            p['xmu'] = numpy.log(p['It']/p['I0'])

        ## use energy as the pandas index
        p.set_index('dcm_energy')
        
        ## comment and separator lines
        handle.write('# //////////////////////////////////////////////////////////\n')
        for l in xdi["_comment"]:
            handle.write(f'# {l}\n')
        handle.write('# ----------------------------------------------------------\n')
        handle.write('# ')

        ## dump the data table and close the file
        handle.write(p.to_csv(None, sep=' ', columns=column_list, index=False, header=column_labels, float_format='%.6f'))
        handle.flush()
        handle.close()

        log_entry(logger, f'wrote XAS data to {fname}')
        #post_to_slack(f'wrote XAS data to {fname}')





        

class SEADFile():

    def to_xdi(self, catalog=None, uid=None, filename=None, logger=None):
        '''Write a single energy absorption detection (SEAD) scan file in XDI
        format, which is a timescan at a specific energy.

        '''
        xdi = catalog[uid].metadata["start"]["XDI"]
        fname = os.path.join(experiment_folder(catalog, uid), filename)
        handle = open(fname, 'w')
        handle.write(f'# XDI/1.0 BlueSky/{bluesky_version} BMM/{pathlib.Path(sys.executable).parts[-3]}\n')

        ## header lines with metadata from the XDi dictionary
        for family in ('Beamline', 'Detector', 'Element', 'Facility', 'Mono', 'Sample', 'Scan'):
            for k in xdi[family].keys():
                if family == 'Sample' and k == 'comment':
                    continue
                if family == 'Sample' and k == 'extra_metadata':
                    continue
                if family == 'Scan' and k == 'edge_energy':
                    handle.write(f'# {family}.mono_energy: {xdi[family][k]}\n')
                else:
                    handle.write(f'# {family}.{k}: {xdi[family][k]}\n')
        start = datetime.datetime.fromtimestamp(catalog[uid].metadata['start']['time']).strftime("%Y-%m-%dT%H:%M:%S") # '%A, %d %B, %Y %I:%M %p')
        end   = datetime.datetime.fromtimestamp(catalog[uid].metadata['stop']['time']).strftime("%Y-%m-%dT%H:%M:%S") # '%A, %d %B, %Y %I:%M %p')
        handle.write(f'# Scan.start_time: {start}\n')
        handle.write(f'# Scan.end_time: {end}\n')
        handle.write(f'# Scan.uid: {uid}\n')
        handle.write(f'# Scan.transient_id: {catalog[uid].metadata["start"]["scan_id"]}\n')
        handle.write( '# Column.1: energy eV\n')
        handle.write( '# Column.2: requested_energy eV\n')
        handle.write( '# Column.3: measurement_time seconds\n')
        handle.write( '# Column.4: xmu\n')
        handle.write( '# Column.5: I0 nA\n')
        handle.write( '# Column.6: It nA\n')
        handle.write( '# Column.7: Ir nA\n')

        ## Column.N header lines
        column_list = ['I0', 'It', 'Ir']
        column_labels = ['time', 'I0', 'It', 'Ir']
        
        el = catalog[uid].metadata['start']['XDI']['Element']['symbol']
        nchan = 0
        if '1-element SDD' in catalog[uid].metadata['start']['detectors']:
            nchan = 1
            column_list.append(f'{el}8')
            column_labels.append(f'{el}8')
            handle.write(f'# Column.8: {el}8\n')
        elif '4-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            nchan = 4
        elif '7-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            nchan = 7
        if nchan > 0:
            for i in range(1, nchan+1):
                handle.write(f'# Column.{i+7}: {el}{i}\n')

        ## prepare data table and insert reltime column
        xa = catalog[uid].primary.read(column_list)
        p = xa.to_pandas()
        t = numpy.array(catalog[uid].primary.data['time'])
        p['time'] = t - t[0]
        column_list.insert(0, 'time')

        ## use time as the pandas index
        p.set_index('time')
        
        ## comment and separator lines
        handle.write('# //////////////////////////////////////////////////////////\n')
        for l in xdi["_comment"]:
            handle.write(f'# {l}\n')
        handle.write('# ----------------------------------------------------------\n')
        handle.write('# ')

        ## dump the data table and close the file
        handle.write(p.to_csv(None, sep=' ', columns=column_list, index=False, header=column_labels, float_format='%.6f'))
        handle.flush()
        handle.close()

        log_entry(logger, f'wrote SEAD data to {fname}')



class LSFile():

    def determine_element(self, catalog, uid):
        labels = list(catalog[uid].primary.read().keys())
        for l in labels:
            m = re.match('^[A-Z][a-z]?[1-7]', l)
            if m is not None:
                return(m.string[:-1])
        return 'MCA'
        
    def to_xdi(self, catalog=None, uid=None, filename=None, logger=None):
        startdoc = catalog[uid].metadata["start"]
        fname = os.path.join(experiment_folder(catalog, uid), filename)
        handle = open(fname, 'w')
        handle.write(f'# XDI/1.0 BlueSky/{bluesky_version} BMM/{pathlib.Path(sys.executable).parts[-3]}\n')

        start = datetime.datetime.fromtimestamp(catalog[uid].metadata['start']['time']).strftime("%Y-%m-%dT%H:%M:%S") # '%A, %d %B, %Y %I:%M %p')
        handle.write(f'# Scan.start_time: {start}\n')
        handle.write(f'# Scan.uid: {uid}\n')
        handle.write(f'# Scan.transient_id: {catalog[uid].metadata["start"]["scan_id"]}\n')

        motor = startdoc["motors"][0]
        column_list = [motor, 'I0', 'It', 'Ir']
        column_labels = [motor, 'I0', 'It', 'Ir']
        
        el = self.determine_element(catalog, uid)
        handle.write(f'# Column.1: {motor}\n')
        handle.write( '# Column.2: I0 nA\n')
        handle.write( '# Column.3: It nA\n')
        handle.write( '# Column.4: Ir nA\n')
        if '1-element SDD' in catalog[uid].metadata['start']['detectors']:
            nchan = 1
            column_list.append(f'{el}8')
            column_labels.append(f'{el}8')
            handle.write(f'# Column.5: {el}8\n')
        elif '4-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4'])
            nchan = 4
        elif '7-element SDD' in catalog[uid].metadata['start']['detectors']:
            column_list.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            column_labels.extend([f'{el}1', f'{el}2', f'{el}3', f'{el}4', f'{el}5', f'{el}6', f'{el}7'])
            nchan = 7
        if nchan > 0:
            for i in range(1, nchan+1):
                handle.write(f'# Column.{i+4}: {el}{i}\n')

        ## prepare data table and insert reltime column
        xa = catalog[uid].primary.read(column_list)
        p = xa.to_pandas()
        t = numpy.array(catalog[uid].primary.data['time'])

        ## use time as the pandas index
        p.set_index(motor)
        
        ## comment and separator lines
        handle.write( '# //////////////////////////////////////////////////////////\n')
        handle.write(f'# linescan on {motor}\n')
        handle.write( '# ----------------------------------------------------------\n')
        handle.write( '# ')

        ## dump the data table and close the file
        handle.write(p.to_csv(None, sep=' ', columns=column_list, index=False, header=column_labels, float_format='%.6f'))
        handle.flush()
        handle.close()

        log_entry(logger, f'wrote linescan data to {fname}')



class RasterFiles():

    def preserve_data(self, catalog, uid, logger):
        '''Save the data from an areascan as a .xlsx file (a simple spreadsheet
        which can be ingested by many plotting programs) and as a .mat
        file (which can be ingested by Matlab).

        to do:
        1. save all Xspress3 columns
        2. 1- and 7-element detectors
        '''

        record  = catalog[uid]
        xlsxout = os.path.join(experiment_folder(catalog, uid), record.metadata['start']['XDI']['_snapshots']['xlsxout'])
        matout  = os.path.join(experiment_folder(catalog, uid), record.metadata['start']['XDI']['_snapshots']['matout'])

        
        motors = record.metadata['start']['motors']
        #print('Reading data set...')
        datatable = record.primary.read()

        slow = numpy.array(datatable[motors[0]])
        fast = numpy.array(datatable[motors[1]])
        i0   = numpy.array(datatable['I0'])
        it   = numpy.array(datatable['It'])
        ir   = numpy.array(datatable['Ir'])

        if '4-element SDD' in catalog[uid].metadata['start']['detectors'] or 'if' in catalog[uid].metadata['start']['detectors'] or 'xs' in catalog[uid].metadata['start']['detectors']:
            det_name = catalog[uid].metadata['start']['plan_name'].split()[-1]
            det_name = det_name[:-1]
            z = numpy.array(datatable[det_name+'1'])+numpy.array(datatable[det_name+'2'])+numpy.array(datatable[det_name+'3'])+numpy.array(datatable[det_name+'4'])
        elif 'noisy_det' in catalog[uid].metadata['start']['detectors']:
            det_name = 'noisy_det'
            z = numpy.array(datatable['noisy_det'])
        else:
            z = numpy.zeros(len(slow))
            
        ## save map in xlsx format
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = record.metadata['start']['XDI']['Sample']['name']
        ws1.append((motors[0], motors[1], f'{det_name}/I0', det_name, 'I0', 'It', 'Ir'))
        for i in range(len(slow)):
            ws1.append((slow[i], fast[i], z[i]/i0[i], z[i], i0[i], it[i], ir[i]))
        wb.save(xlsxout)
        log_entry(logger, f'wrote {xlsxout}')

        ## save map in matlab format 
        savemat(matout, {'label'   : record.metadata['start']['XDI']['Sample']['name'],
                         motors[0] : list(slow),
                         motors[1] : list(fast),
                         'I0'      : list(i0),
                         'It'      : list(it),
                         'Ir'      : list(ir),
                         'signal'  : list(z),})
        log_entry(logger, f'wrote {matout}')

