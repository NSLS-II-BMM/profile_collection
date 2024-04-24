import os, re, socket, ast, datetime
from urllib.parse import quote
import numpy
import logging

logger = logging.getLogger('BMM file manager logger')
logger.handlers = []


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

startup_dir = os.path.dirname(__file__)

class BMMDossier():
    '''A class for generating a static HTML file for documenting an XAS
    measurement at BMM.

    The concept is that the (many, many) attributes of this class will
    be accumulated as the scan plan is executed.  At the end of the
    scan sequence, the static HTML file will be generated.

    That static HTML file is made using a set of simple text templates
    which are filled in, the concatenated in a way that suitable for
    the current XAS measurement.

    It is the responsibility of the process sending the kafka messages
    to supply EVERY SINGLE ONE of the attributes.  

    attributes
    ==========
    anacam_uid : str or None
      UID for the analog camera image
    analog_file : str
      fully resolved path/filename for the analog camera image
    anasnap : str
      filename without path for analog file image
    bounds : str
      stringified list of XAFS scan boundaries
    cif : str
      DOI or URL for relevant CIF file
    clargs : str
      stringification of arguments to the xafs() plan
    comment : str 
      user-supplied comment text
    date : str
      start date of experiment
    doi : str
      DOI for relevant publication
    edge : str
      edge symbol
    element : str
      1- or 2-letter element symbol
    end : str
      last scan number in sequence
    experimenters : str
      names of experiments written as First1 Last1, First2 Last2, etc
    filename : str
      filename stub for XAFS data files
    folder : str
      target data folder
    gup : str
      general (partner) user proposal number
    htmlpage : str
      True is the dossier is to be written
    inifile : str
      fully resolved path and name of INI file in use
    initext : str
      string with concatination of the lines of inifile
    instrument : str
      html text for instrument DIV, supplied by instrument class
    measurement : str
      XAFS, raster, time
    mode : str
      XAFS measurement mode, usually fluorescence, transmission, or reference
    mono : str
      string describing mono Si(111), Si(311), or Si(333)
    motors : str
      outout of motor_sidebar function
    ocrs : str
      stringification of OCR values for the detector elements
    pccenergy : str
      pseudo channel-cut energy value
    pdstext : str
      text describing PDS mode, usually concatination of get_mode() and describe_mode()
    post_anacam : str
      True to post anacam image to Slack
    post_usbcam1 : str
      True to post usbcam1 image to Slack
    post_usbcam2 : str
      True to post usbcam2 image to Slack
    post_webcam : str
      True to post webcam image to Slack
    post_xrf : str
      True to post XRF plot to Slack
    prep : str
      user-supplied sample preparation text
    rid : str
      reference ID number for link to Slack message log capture
    rois : str
      stringification of ROI values for the detector elements
    saf : str
      safety approval form number for the experiment
    sample : str
      user-supplied sample description
    scanlist : str
      generated HTML text for the sample list sidebar
    seqend : str
      end time for scan sequence
    seqstart : str
      start time for scan sequence      
    start : str
      initial scan number
    steps : str
      stringified list of XAFS scan step sizes      
    ththth : str
      True if using the Si(333) mono
    times : str
      stringified list of XAFS scan dwell times      
    uidlist : list of str
      generated list of XAFS scan UIDs in the scan sequence
    url : str
      URL relevant to the sample or experiment
    usbcam1_file : str
      fully resolved path/filename for the USB1 image
    usbcam1_uid : str
      UID for the USB1 image
    usb1snap : str
      filename without path for USB1 image
    usbcam2_file : str
      fully resolved path/filename for the USB2 image
    usbcam2_uid : str
      UID for the USB2 image
    usb2snap : str
      filename without path for USB2 image
    webcam_file : str
      fully resolved path/filename for the webcam image
    webcam_uid : str
      UID for the webcam image
    websnap : str
      filename without path for webcam image
    xrf_image : str
      fully resolved path/filename for the image of the XRF plot
    xrf_uid : str
      UID for the XRF measurement before the scan sequence      
    xrffile : str
      fully resolved path/filename for the XRF data file
    xrfsnap : str
      filename without path for the XRF data file

    methods
    =======
    capture_xrf
      measure an XRF spectrum and capture its metadata for use in a dossier

    cameras
      take a snapshot with each camera and capture metadata for use in a dossier

    prep_metadata
      organize metadata common to any dossier

    write_dossier
       generate the sample specific dossier file for an XAFS measurement

    raster_dossier
       generate the sample specific dossier file for a raster measurement
    
    sead_dossier
       generate the sample specific dossier file for a SEAD measurement
    
    write_manifest
       update the manifest and the 00INDEX.html file

    make_merged_triplot
       merge the scans and generate a triplot

    simple_plot
       simple, fallback plot

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

    ## these default values should still allow a dossier to be written
    ## even if parameters were not provided by the process sending the
    ## kafka message
    anacam_uid = None
    anacam_file = ''
    anasnap = ''
    bounds = ''
    cif = ''
    clargs = ''
    comment = ''
    date = ''
    doi = ''
    edge = 'K'
    element = 'Fe'
    end = 1
    experimenters = ''
    filename = ''
    folder = ''
    gup = ''
    htmlpage = True
    inifile = ''
    initext = ''
    instrument = ''
    measurement = 'XAFS'
    mode = 'fluorescence'
    mono = ''
    motors = ''
    ocrs = ''
    pccenergy = 10000
    pdstext = ''
    post_anacam = False
    post_usbcam1 = False
    post_usbcam2 = False
    post_webcam = False
    post_xrf = False
    prep = ''
    rid = ''
    rois = ''
    saf = ''
    sample = ''
    scanlist = ''
    seqend = ''
    seqstart = ''
    start = 1
    steps = ''
    ththth = False
    times = ''
    uidlist = []
    url = ''
    usbcam1_file =''
    usbcam1_uid = None
    usb1snap = ''
    usbcam2_file = ''
    usbcam2_uid = None
    usb2snap = ''
    webcam_file = ''
    webcam_uid = None
    websnap = ''
    xrf_image = ''
    xrf_uid = None
    xrffile = ''
    xrfsnap = ''


    ## another dossier type...?
    npoints       = 0
    dwell         = 0
    delay         = 0
    scanuid       = None


    def __init__(self):
        self.scanlist      = ''
        #self.motors        = motor_sidebar()
        #self.manifest_file = os.path.join(user_ns['BMMuser'].folder, 'dossier', 'MANIFEST')

    def clear_logger(self):
        logger.handlers = []
            
    def establish_logger(self):
        folder = rkvs.get('BMM:user:folder').decode('UTF8')
        log_master_file = os.path.join(folder, 'file_manager.log')
        if not os.path.isfile(log_master_file):
            os.mknod(log_master_file)
        logging.basicConfig(filename=log_master_file, encoding='utf-8', level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n')
        print(f'established a logging handler for experiment in {folder}')

        
    def set_parameters(self, **kwargs):
        for k in kwargs.keys():
            if k == 'dossier':
                continue
            else:
                setattr(self, k, kwargs[k])

    def log_entry(self, message):
        print(message)
        logger.info(message)


    def write_dossier(self, bmm_catalog):

        if len(self.uidlist) == 0:
            self.log_entry('*** cannot write dossier, uidlist is empty')
            return None

        ## gather information for the dossier from the start document
        ## of the first scan in the sequence
        startdoc = bmm_catalog[self.uidlist[0]].metadata['start']
        XDI = startdoc['XDI']
        if '_snapshots' in XDI:
            snapshots = XDI['_snapshots']
        else:
            snapshots = {}
        
        
        
        ## test if XAS data file can be found
        if self.filename is None or self.start is None:
            self.log_entry('*** Filename and/or start number not given.  (xafs_dossier).')
            return None
        firstfile = f'{XDI["_user"]["filename"]}.{XDI["_user"]["start"]:03d}'
        if not os.path.isfile(os.path.join(self.folder, firstfile)):
            self.log_entry(f'*** Could not find {os.path.join(self.folder, firstfile)}')
            return None

        ## determine names of output dossier files
        basename     = self.filename
        htmlfilename = os.path.join(self.folder, 'dossier/', self.filename+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(self.folder, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))):
                seqnumber += 1
            basename     = "%s-%2.2d" % (self.filename,seqnumber)
            htmlfilename = os.path.join(self.folder, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))

        ## generate triplot as a png image (or fail gracefully)
        prjfilename, pngfilename = None, None
        try:
            if self.uidlist is not None:
                pngfilename = os.path.join(self.folder, 'snapshots', f"{basename}.png")
                #prjfilename = os.path.join(self.folder, 'prj', f"{basename}.prj")
                self.make_merged_triplot(self.uidlist, pngfilename, XDI['_user']['mode'])
        except Exception as e:
            logger.info('*** failure to make triplot\n' + str(e))


        ## sanity check the "report ID" (used to link to correct position in messagelog.html
        if self.rid is None: self.rid=''

        try:
            # dossier header
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_top.tmpl')) as f:
                content = f.readlines()
            thiscontent = ''.join(content).format(measurement   = 'XAFS',
                                                  filename      = XDI['_user']['filename'],
                                                  date          = self.date,
                                                  rid           = self.rid,
                                                  seqnumber     = seqnumber, )

            # left sidebar, entry for XRF file in the case of fluorescence data
            thismode = self.plotting_mode()
            if thismode == 'xs' or thismode == 'xs1':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(basename      = basename,
                                                       xrffile       = quote('../XRF/'+os.path.basename(XDI['_xrffile'])),
                                                       xrfuid        = self.xrf_uid, )

            # middle part of dossier
            if self.instrument == '':
                self.instrument = '<div></div>'
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_middle.tmpl')) as f:
                content = f.readlines()
            thiscontent += ''.join(content).format(basename      = basename,
                                                   scanlist      = generate_scanlist(self, bmm_catalog),  # uses self.uidlist
                                                   motors        = self.motors,
                                                   sample        = XDI['Sample']['name'],
                                                   prep          = XDI['Sample']['prep'],
                                                   comment       = XDI['_user']['comment'],
                                                   instrument    = self.instrument,)
            

            # middle part, cameras, one at a time and only if actually snapped
            if 'webcam_uid' in snapshots:
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+os.path.basename(snapshots['webcam_file'])),
                                                       uid         = _snapshots['webcam_uid'],
                                                       camera      = 'webcam',
                                                       description = 'XAS web camera', )
            if 'anacam_uid' in snapshots:
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+os.path.basename(snapshots['analog_file'])),
                                                       uid         = snapshots['anacam_uid'],
                                                       camera      = 'anacam',
                                                       description = 'analog pinhole camera', )
            if 'usbcam1_uid' in snapshots:
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+os.path.basename(snapshots['usb1_file'])),
                                                       uid         = snapshots['usbcam1_uid'],
                                                       camera      = 'usbcam1',
                                                       description = 'USB camera #1', )
            if 'usbcam2_uid' in snapshots:
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+os.path.basename(snapshots['usb2_file'])),
                                                       uid         = snapshots['usbcam2_uid'],
                                                       camera      = 'usb2cam',
                                                       description = 'USB camera #2', )
            
            # middle part, XRF and glancing angle alignment images
            if thismode == 'xs' or thismode == 'xs1':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_image.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(xrfsnap       = quote('../XRF/'+os.path.basename(snapshots['xrf_image'])),
                                                       pccenergy     = '%.1f' % XDI['_user']['_pccenergy'],
                                                       ocrs          = self.ocrs,
                                                       rois          = self.rois,
                                                       symbol        = XDI['Element']['symbol'],)
                if 'glancing' in self.instrument:
                    with open(os.path.join(startup_dir, 'tmpl', 'dossier_ga.tmpl')) as f:
                        content = f.readlines()
                    thiscontent += ''.join(content).format(ga_align      = ga.alignment_filename,
                                                           ga_yuid       = ga.y_uid,
                                                           ga_puid       = ga.pitch_uid,
                                                           ga_fuid       = ga.f_uid, )

            # end of dossier
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_bottom.tmpl')) as f:
                content = f.readlines()
            this_ref = all_references[XDI['Element']['symbol']][3]
            thiscontent += ''.join(content).format(e0            = '%.1f' % edge_energy(XDI['Element']['symbol'], XDI['Element']['edge']),
                                                   edge          = XDI['Element']['edge'],
                                                   element       = self.element_text(XDI['Element']['symbol']),
                                                   mode          = XDI['_user']['mode'],
                                                   bounds        = ", ".join(XDI['_user']['bounds_given']),
                                                   steps         = XDI['_user']['steps'],
                                                   times         = XDI['_user']['times'],
                                                   reference     = re.sub(r'(\d+)', r'<sub>\1</sub>', this_ref),
                                                   seqstart      = datetime.datetime.fromtimestamp(startdoc['start']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                                   seqend        = datetime.datetime.fromtimestamp(bmm_catalog[self.uidlist[-1]].metadata['stop']['time']).strftime('%A, %B %d, %Y %I:%M %p'),
                                                   mono          = self.mono,
                                                   pdsmode       = self.pdstext,
                                                   pccenergy     = '%.1f' % XDI['_user']['_pccenergy'],
                                                   experimenters = XDI['_user']['experimenters'],
                                                   gup           = XDI['Facility']['GUP'],
                                                   saf           = XDI['Facility']['GUP'],
                                                   url           = XDI['_user']['url'],
                                                   doi           = XDI['_user']['doi'],
                                                   cif           = XDI['_user']['cif'],
                                                   initext       = highlight(XDI['_user']['initext'], IniLexer(),    HtmlFormatter()),
                                                   clargs        = highlight(XDI['_user']['clargs'],  PythonLexer(), HtmlFormatter()),
                                                   filename      = XDI['_user']['filename'],)

            with open(htmlfilename, 'a') as o:
                o.write(thiscontent)

            self.log_entry(f'wrote dossier: {htmlfilename}')
        except Exception as E:
            self.log_entry(f'failed to write dossier file {htmlfilename}\n' + E)







    def plotting_mode(self):
        self.mode = self.mode.lower()
        if self.mode == 'xs1':
            return 'xs1'
        elif any(x in self.mode for x in ('xs', 'fluo', 'flou', 'both')):
            return 'xs'
        #elif any(x in self.mode for x in ('fluo', 'flou', 'both')):
        #    return 'fluo'  # deprecated analog fluo detection
        elif self.mode == 'ref':
            return 'ref'
        elif self.mode == 'yield':
            return 'yield'
        elif self.mode == 'test':
            return 'test'
        elif self.mode == 'icit':
            return 'icit'
        elif self.mode == 'ici0':
            return 'ici0'
        else:
            return 'trans'

    def element_text(self, element='Po'):
        if Z_number(element) is None:
            return ''
        else:
            thistext  = f'{element} '
            thistext += f'(<a href="https://en.wikipedia.org/wiki/{element_name(element)}">'
            thistext += f'{element_name(element)}</a>, '
            thistext += f'{Z_number(element)})'
            return thistext
        
    def generate_scanlist(self, bmm_catalog):
        template = '<li><a href="../{filename}.{ext}" title="Click to see the text of {filename}.{ext}">{filename}.{ext}</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="javascript:void(0)" onclick="toggle_visibility(\'{filename}.{ext}\');" title="This is the scan number for {filename}.{ext}, click to show/hide its UID">#{scanid}</a><div id="{filename}.{ext}" style="display:none;"><small>{uid}</small></div></li>\n'

        text = ''
        ext = bmm_catalog[self.uidlist[0]].metadata['start']['XDI']['_user']['start']
        for u in self.uidlist:
            text += template.format(filename = bmm_catalog[u].metadata['start']['XDI']['_user']['filename'],
                                    ext      = ext,
                                    scanid   = bmm_catalog[u].metadata['start']['scan_id'],
                                    uid      = u)
            ext = ext + 1
        return text


    def motor_sidebar(self, bmm_catalog):
        baseline = bmm_catalog[self.uidlist[0]].baseline.read()

        '''Generate a list of motor positions to be used in the static html page for a scan sequence.
        Return value is a long string with html tags and entities embedded in the string.

        Parameters
        ----------
        md : dict
            dict with motor positions keyed by <motor>.name

        If md is not provided, the current motor positions will be used.
        If taking a record from Data Broker, the motor positions have been
        recorded in the baseline.  If generating a dossier from a Data
        Broker record, do:

        >>> text = motor_sidebar(uid=uid)

        where uid is the ID of the scan.
        '''
        if type(md) == str:
            md = motor_metadata(md)
        if md is None or type(md) is not dict:
            md = motor_metadata()
        motors = ''

        motors +=  '<span class="motorheading">XAFS stages:</span>\n'
        motors +=  '            <div id="motorgrid">\n'
        motors += f'              <div>xafs_x, {baseline["xafs_linx"][0]:.3f}</div>\n'
        motors += f'              <div>xafs_y, {baseline["xafs_liny"][0]:.3f}</div>\n'
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
        motors += f'              <div>slot, {user_ns["xafs_wheel"].current_slot():.3f}</div>\n'
        motors += f'              <div>spinner, {user_ns["ga"].current():.3f}</div>\n'
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
        motors += f'              <div>m2_bender, {baseline["m2_bender"]"][0]:.3f}</div>\n'
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
        
