import os
from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter
from urllib.parse import quote
import numpy

import matplotlib
import matplotlib.pyplot as plt
from larch.io import create_athena

from BMM.functions       import plotting_mode, error_msg, whisper, etok
from BMM.larch_interface import Pandrosus, Kekropidai
from BMM.logging         import img_to_slack, post_to_slack
from BMM.modes           import get_mode, describe_mode
from BMM.motor_status    import motor_sidebar
from BMM.periodictable   import edge_energy, Z_number, element_name

from BMM.user_ns.base import db, startup_dir

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

class BMMDossier():
    '''A class for generating a static HTML file for documenting an XAS
    measurement at BMM.

    The concept is that the (many, many) attributes of this class will
    be accumulated as the scan plan is executed.  At the end of the
    scan sequence, the static HTML file will be generated.

    That static HTML file is made using a set of simple text templates
    which are filled in, the concatenated in a way that suitable for
    the current XAS measurement.

    attributes
    ==========
    inifile : str
      the INI file used for the xafs() plan
    filename : str
      the filename argument fro the INI file
    start : int
      the starting extension number of this scan sequence
    end : int
      the ending extension number of this scan sequence
    experimenters : str
      names of the people involved
    seqstart : datetime string
      the start time of the scan sequence (usually taken from the start document
    seqend : datetime string
      the end time of the scan sequence (usually taken from the stop document
    e0 : float
      the e0 vale of the scan
    edge : str
      the edge symbol (K, L1, L2, or L3)
    element : str
      the one- or two letter element symbol
    scanlist :

    motors : str
      the output of motor_sidebar()
    sample : str
      the user-supplied sample composition or stoichiometry
    prep : str
      the user-supplied sample preparation description
    comment : str
      the user-supplied comment string
    mode : str
      the plotting mode (transmission, fluorescence, both, reference, yield)
    pccenergy : float
      the energy at which the mono was put into pseudo-channel-cut mode
    bounds : str
      the boundaries of the XAS step scan
    steps : str
      the step sizes of the XAS step scan
    times : strftime
      the integration times of the XAS step scan
    clargs : str
      a dict of command line arguments to the xafs() plan
    websnap : str
      the filename of the image from the XAS webcam
    webuid : str
      the UID of the XAS webcam exposure
    anasnap : str
      the filename of the image from the analog pinhole camera
    anauid : str
      the UID of the analog pinhole camera exposure
    usb1snap : str
      the filename of the image from the first USB webcam
    usb1uid : str
      the UID of the first USB camera exposure
    usb2snap : str
      the filename of the image from the second USB camera
    usb2uid : str
      the UID of the second USB camera exposure
    xrfsnap : str
      the filename of the XRF image
    xrffile : str
      the filename of the XRF data
    xrfuid : str
      the UID of the Xspress3 XRF webcam exposure
    ocrs : str
      stringification of the OCR values from the XRF exposure
    rois : str
      stringification of the ROI values from the XRF exposure
    htmlpage : bool
      true if writing this html page
    ththth : bool
      true if using the Si(333) reflection
    initext : str
      INI file as a slurped-in text string
    uidlist : list
      list of XAS scan UIDs
    url : str
      user-supplied URL
    doi : str
      user-supplied DOI link
    cif : str
      user-supplied link to a CIF file

    instrument : str
      description of instrument state, see below

    methods
    =======
    write_dossier
       generate the sample specific dossier file
    
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
              thistext  =  '	    <div id="boxinst">\n'
              thistext +=  '	      <h3>Instrument: Glancing angle stage</h3>\n'
              thistext +=  '	      <ul>\n'
              thistext += f'               <li><b>Spinner:</b> {self.current()}</li>\n'
              thistext += f'               <li><b>Tilt angle:</b> {xafs_pitch.position - self.flat[1]:.1f}</li>\n'      
              thistext += f'               <li><b>Spinning:</b> {"yes" if self.spin else "no"}</li>\n'
              thistext +=  '	      </ul>\n'
              thistext +=  '	    </div>\n'
              return thistext

    This returns a <div> block for the HTML dossier file with
    id="boxinst", which identifies the div for the CSS formatting.
    The contents of this text include a header3 description of the
    instrument and an unordered list of the most salient aspects of
    the current state of the instrument.

    Admittedly, requiring a method that generates suitable HTML is a
    bit unwieldy, but is allows much flexibility in how the instrument
    gets described in the dossier.

    The dossier_entry methods get used in BMM/xafs.py around line 880.

    '''
    inifile       = None
    filename      = None
    start         = None
    end           = None
    experimenters = None
    seqstart      = None
    seqend        = None
    e0            = None
    edge          = None
    element       = None
    sample        = None
    prep          = None
    comment       = None
    mode          = None
    pccenergy     = None
    bounds        = None
    steps         = None
    times         = None
    clargs        = ''
    websnap       = ''
    webuid        = ''
    anasnap       = ''
    anauid        = ''
    usb1snap      = ''
    usb1uid       = ''
    usb2snap      = ''
    usb2uid       = ''
    xrfsnap       = ''
    xrffile       = ''
    xrfuid        = ''
    ocrs          = ''
    rois          = ''
    htmlpage      = None
    ththth        = None
    uidlist       = None
    url           = None
    doi           = None
    cif           = None
    instrument    = ''

    initext       = None


    def __init__(self):
        self.scanlist      = ''
        self.motors        = motor_sidebar()
        self.manifest_file = os.path.join(user_ns['BMMuser'].DATA, 'dossier', 'MANIFEST')

    def write_dossier(self):
        BMMuser, dcm, ga = user_ns['BMMuser'], user_ns['dcm'], user_ns['ga']
        if self.filename is None or self.start is None:
            print(error_msg('Filename and/or start number not given.'))
            return None
        firstfile = f'{self.filename}.{self.start:03d}'
        if not os.path.isfile(os.path.join(BMMuser.DATA, firstfile)):
            print(error_msg(f'Could not find {os.path.join(BMMuser.DATA, firstfile)}'))
            return None

        # figure out various filenames
        basename     = self.filename
        htmlfilename = os.path.join(BMMuser.DATA, 'dossier/', self.filename+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(BMMuser.DATA, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))):
                seqnumber += 1
            basename     = "%s-%2.2d" % (self.filename,seqnumber)
            htmlfilename = os.path.join(BMMuser.DATA, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))

        ## generate triplot as a png image (or fail gracefully)
        prjfilename, pngfilename = None, None
        try:
            if self.uidlist is not None:
                pngfilename = os.path.join(BMMuser.DATA, 'snapshots', f"{basename}.png")
                #prjfilename = os.path.join(BMMuser.DATA, 'prj', f"{basename}.prj")
                self.make_merged_triplot(self.uidlist, pngfilename, self.mode)
        except Exception as e:
            print(error_msg('failure to make triplot'))
            print(e)

        # slurp in the INI file contents
        if self.initext is None:
            with open(os.path.join(BMMuser.DATA, self.inifile)) as f:
                self.initext = ''.join(f.readlines())

        # gather some information about the photon delivery system
        pdstext = f'{get_mode()} ({describe_mode()})'
        mono = 'Si(%s)' % dcm._crystal
        if self.ththth:
            mono = 'Si(333)'

        try:
            # dossier header
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_top.tmpl')) as f:
                content = f.readlines()
            thiscontent = ''.join(content).format(filename      = self.filename,
                                                  date          = BMMuser.date,
                                                  seqnumber     = seqnumber, )

            # left sidebar, entry for XRF file in the case of fluorescence data
            thismode = plotting_mode(self.mode)
            if thismode == 'xs' or thismode == 'xs1':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(basename      = basename,
                                                       xrffile       = quote('../XRF/'+str(self.xrffile)),
                                                       xrfuid        = self.xrfuid, )

            # middle part of dossier
            if self.instrument == '':
                self.instrument = '<div id=boxinst><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p></div>'
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_middle.tmpl')) as f:
                content = f.readlines()
            thiscontent += ''.join(content).format(basename      = basename,
                                                   scanlist      = self.scanlist,
                                                   motors        = self.motors,
                                                   sample        = self.sample,
                                                   prep          = self.prep,
                                                   comment       = self.comment,
                                                   instrument    = self.instrument,
                                                   websnap       = quote('../snapshots/'+self.websnap),
                                                   webuid        = self.webuid,
                                                   anasnap       = quote('../snapshots/'+self.anasnap),
                                                   anauid        = self.anauid,
                                                   usb1snap      = quote('../snapshots/'+self.usb1snap),
                                                   usb1uid       = self.usb1uid,
                                                   usb2snap      = quote('../snapshots/'+self.usb2snap),
                                                   usb2uid       = self.usb2uid, )
            
            # middle part, XRF and glancing angle alignment images
            if thismode == 'xs' or thismode == 'xs1':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_image.tmpl')) as f:
                    content = f.readlines()
                thiscontent += ''.join(content).format(xrfsnap       = quote('../XRF/'+str(self.xrfsnap)),
                                                       pccenergy     = '%.1f' % self.pccenergy,
                                                       ocrs          = self.ocrs,
                                                       rois          = self.rois,
                                                       symbol        = self.element,)
                if 'glancing' in BMMuser.instrument:
                    with open(os.path.join(startup_dir, 'tmpl', 'dossier_ga.tmpl')) as f:
                        content = f.readlines()
                    thiscontent += ''.join(content).format(ga_align      = ga.alignment_filename,
                                                           ga_yuid       = ga.y_uid,
                                                           ga_puid       = ga.pitch_uid,
                                                           ga_fuid       = ga.f_uid, )

            # end of dossier
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_bottom.tmpl')) as f:
                content = f.readlines()
            thiscontent += ''.join(content).format(e0            = '%.1f' % self.e0,
                                                   edge          = self.edge,
                                                   element       = self.element_text(),
                                                   mode          = self.mode,
                                                   bounds        = self.bounds,
                                                   steps         = self.steps,
                                                   times         = self.times,
                                                   seqstart      = self.seqstart,
                                                   seqend        = self.seqend,
                                                   mono          = mono,
                                                   pdsmode       = pdstext,
                                                   pccenergy     = '%.1f' % self.pccenergy,
                                                   experimenters = self.experimenters,
                                                   gup           = BMMuser.gup,
                                                   saf           = BMMuser.saf,
                                                   url           = self.url,
                                                   doi           = self.doi,
                                                   cif           = self.cif,
                                                   initext       = highlight(self.initext, IniLexer(), HtmlFormatter()),
                                                   clargs        = highlight(self.clargs, PythonLexer(), HtmlFormatter()),
                                                   filename      = self.filename,)


            with open(htmlfilename, 'a') as o:
                o.write(thiscontent)

            print(f'wrote {htmlfilename}')
        except Exception as E:
            print(E)

        manifest = open(self.manifest_file, 'a')
        manifest.write(f'xafs␣{htmlfilename}\n')
        manifest.close()
        self.write_manifest()

        if pngfilename is not None and os.path.isfile(pngfilename):
            try:
                img_to_slack(pngfilename)
            except:
                post_to_slack(f'failed to post image: {pngfilename}')
                pass

        return htmlfilename

    
    def write_manifest(self, scantype='XAFS'):
        '''Update the scan manifest and the corresponding static html file.'''
        BMMuser = user_ns['BMMuser']
        with open(self.manifest_file) as f:
            lines = [line.rstrip('\n') for line in f]

        experimentlist = ''
        for l in lines:
            (scantype, fname) = l.split('␣')
            if not os.path.isfile(fname):
                continue
            this = os.path.basename(fname)
            experimentlist += f'<li>{scantype}: <a href="./{this}">{this}</a></li>\n'

        #with open(os.path.join(BMMuser.DATA, 'dossier', 'manifest.tmpl')) as f:
        with open(os.path.join(startup_dir, 'tmpl', 'manifest.tmpl')) as f:
            content = f.readlines()
        indexfile = os.path.join(BMMuser.DATA, 'dossier', '00INDEX.html')
        o = open(indexfile, 'w')
        o.write(''.join(content).format(date           = BMMuser.date,
                                        experimentlist = experimentlist,))
        o.close()


    def element_text(self):
        if Z_number(self.element) is None:
            return ''
        else:
            thistext  = f'{self.element} '
            thistext += f'(<a href="https://en.wikipedia.org/wiki/{element_name(self.element)}">'
            thistext += f'{element_name(self.element)}</a>, '
            thistext += f'{Z_number(self.element)})'
            return thistext
        

    def make_merged_triplot(self, uidlist, filename, mode):
        '''Make a pretty, three panel plot of the data from the scan sequence
        just finished.

        '''
        BMMuser = user_ns['BMMuser']
        cnt = 0
        try:
            base = Pandrosus()
            projname = os.path.join(BMMuser.folder, 'prj', os.path.basename(filename)).replace('.png', '.prj')
            proj = create_athena(projname)
            base.fetch(uidlist[0], mode=mode)
            ee = base.group.energy
            mm = base.group.mu
            save = base.group.args['label']
            ## hardwire a fix for an odd larch/athena interaction
            base.group.args['bkg_spl2'] = etok(float(base.group.args['bkg_spl2e']))
            proj.add_group(base.group)
            base.group.args['label'] = save
            cnt = 1
            if len(uidlist) > 1:
                for uid in uidlist[1:]:
                    this = Pandrosus()
                    try:
                        this.fetch(uid, mode=mode)
                        mu = numpy.interp(ee, this.group.energy, this.group.mu)
                        mm = mm + mu
                        save = this.group.args['label']
                        this.group.args['bkg_spl2'] = etok(float(this.group.args['bkg_spl2e']))
                        proj.add_group(this.group)
                        this.group.args['label'] = save
                        cnt += 1
                    except Exception as E:
                        print(E)
                        pass # presumably this is noisy data for which a valid background was not found
        except Exception as E:
            print(E)
            pass # presumably this is noisy data for which a valid background was not found
        if cnt == 0:
            print(whisper(f'Unable to make triplot'))
            try:
                self.simple_plot(uidlist, filename, mode)
            except:
                print(whisper(f'Also unable to make simple plot'))
            return
        mm = mm / cnt
        merge = Pandrosus()
        merge.put(ee, mm, 'merge')
        thisagg = matplotlib.get_backend()
        matplotlib.use('Agg') # produce a plot without screen display
        merge.triplot()
        plt.savefig(filename)
        print(whisper(f'Wrote triplot to {filename}'))
        matplotlib.use(thisagg) # return to screen display
        ## hardwire a fix for an odd larch/athena interaction
        for a in proj.groups:
            if hasattr(proj.groups[a], 'args'):
                proj.groups[a].args['bkg_spl2'] = etok(float(proj.groups[a].args['bkg_spl2e']))
        proj.save()
        print(whisper(f'Wrote Athena project to {projname}'))
        #return(proj)


    def simple_plot(self, uidlist, filename, mode):
        '''If the triplot cannot be made for some reason, make a fallback,
        much simpler plot so that something is available for Slack and
        the dossier.

        '''
        BMMuser = user_ns['BMMuser']
        this = db.v2[uidlist[0]].primary.read()
        if mode == 'test':
            title, ylab = 'XAS test scan', 'I0 (nA)'
            signal = this['I0']
        elif mode == 'transmission':
            title, ylab = '', 'transmission'
            signal = numpy.log(numpy.abs(this['I0']/this['It']))
        elif mode == 'reference':
            title, ylab = '', 'reference'
            signal = numpy.log(numpy.abs(this['It']/this['Ir']))
        elif mode == 'yield':
            title, ylab = '', 'yield'
            signal = this['Iy']/this['I0']
        elif mode == 'xs1':
            title, ylab = '', 'fluorescence'
            signal = (this[BMMuser.xs8]+0.001)/(this['I0']+1)
        else:
            title, ylab = '', 'fluorescence'
            signal = (this[BMMuser.xs1]+this[BMMuser.xs2]+this[BMMuser.xs3]+this[BMMuser.xs4]+0.001)/(this['I0']+1)
            
        thisagg = matplotlib.get_backend()
        matplotlib.use('Agg') # produce a plot without screen display
        plt.cla()
        plt.title(title)
        plt.xlabel('energy (eV)')
        plt.ylabel(ylab)
        plt.plot(this['dcm_energy'], signal)
        plt.savefig(filename)
        matplotlib.use(thisagg) # return to screen display
        print(whisper(f'Wrote simple plot to {filename}'))
            

    def raster_instrument_entry(self):
        thistext  =  '      <div id="boxinst">\n'
        thistext +=  '        <h3>Instrument: Raster scan</h3>\n'
        thistext += f'          <a href="../maps/{self.pngout}">\n'
        thistext += f'                        <img src="../maps/{self.pngout}" width="300" alt="" /></a>\n'
        thistext +=  '          <br>'
        thistext += f'          <a href="javascript:void(0)" onclick="toggle_visibility(\'areascan\');" title="Click to show/hide the UID of this areascan">(uid)</a><div id="areascan" style="display:none;"><small>{self.scanuid}</small></div>\n'
        thistext +=  '      </div>\n'
        return thistext


    def raster_dossier(self):
        print(whisper('writing raster dossier'))
        BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
        if self.filename is None:
            print(error_msg('Filename not given.'))
            return None

        # figure out various filenames
        self.basename = self.filename
        htmlfilename = os.path.join(BMMuser.DATA, 'dossier/', self.filename+'-01.html')
        seqnumber = 1
        if os.path.isfile(htmlfilename):
            seqnumber = 2
            while os.path.isfile(os.path.join(BMMuser.DATA, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))):
                seqnumber += 1
            self.basename = "%s-%2.2d" % (self.filename,seqnumber)
            htmlfilename = os.path.join(BMMuser.DATA, 'dossier', "%s-%2.2d.html" % (self.filename,seqnumber))

        # slurp in the INI file contents
        if self.initext is None:
            with open(os.path.join(BMMuser.DATA, self.inifile)) as f:
                self.initext = ''.join(f.readlines())

        # gather some information about the photon delivery system
        pdstext = f'{get_mode()} ({describe_mode()})'
        mono = 'Si(%s)' % dcm._crystal
        if self.ththth:
            mono = 'Si(333)'

        with open(os.path.join(startup_dir, 'tmpl', 'raster.tmpl')) as f:
                content = f.readlines()
        thiscontent = ''.join(content).format(filename      = self.filename,
                                              basename      = self.basename,
                                              date          = BMMuser.date,
                                              seqnumber     = seqnumber,
                                              e0            = '%.1f' % self.e0,
                                              edge          = self.edge,
                                              element       = self.element_text(),
                                              sample        = self.sample,
                                              prep          = self.prep,
                                              comment       = self.comment,
                                              instrument    = self.raster_instrument_entry(),
                                              fast_motor    = self.fast_motor,
                                              slow_motor    = self.slow_motor,
                                              fast_init     = self.fast_init,
                                              slow_init     = self.slow_init,
                                              websnap       = quote('../snapshots/'+self.websnap),
                                              webuid        = self.webuid,
                                              anasnap       = quote('../snapshots/'+self.anasnap),
                                              anauid        = self.anauid,
                                              usb1snap      = quote('../snapshots/'+self.usb1snap),
                                              usb1uid       = self.usb1uid,
                                              usb2snap      = quote('../snapshots/'+self.usb2snap),
                                              usb2uid       = self.usb2uid,
                                              pngout        = self.pngout,
                                              xlsxout       = self.xlsxout,
                                              matout        = self.matout,
                                              mode          = self.mode,
                                              motors        = self.motors,
                                              bounds        = self.bounds,
                                              steps         = self.steps,
                                              times         = self.times,
                                              seqstart      = self.seqstart,
                                              seqend        = self.seqend,
                                              mono          = mono,
                                              pdsmode       = pdstext,
                                              experimenters = self.experimenters,
                                              gup           = BMMuser.gup,
                                              saf           = BMMuser.saf,
                                              url           = self.url,
                                              doi           = self.doi,
                                              cif           = self.cif,
                                              initext       = highlight(self.initext, IniLexer(), HtmlFormatter()),
                                              clargs        = highlight(self.clargs, PythonLexer(), HtmlFormatter()),
        )
        with open(htmlfilename, 'a') as o:
            o.write(thiscontent)

        print(f'wrote {htmlfilename}')

        manifest = open(self.manifest_file, 'a')
        manifest.write(f'raster␣{htmlfilename}\n')
        manifest.close()
        self.write_manifest()
