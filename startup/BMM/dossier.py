import os
from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter
from urllib.parse import quote

import matplotlib
import matplotlib.pyplot as plt
from larch.io import create_athena

from BMM.functions       import plotting_mode, error_msg, whisper
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

    methods
    =======
    write_dossier
       generate the sample specific dossier file
    
    write_manifest
       update the manifest and the 00INDEX.html file

    make_merged_triplot
       merge the scans and generate a triplot

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

    initext       = None


    def __init__(self):
        self.scanlist      = ''
        self.motors        = motor_sidebar()
        self.manifest_file = os.path.join(user_ns['BMMuser'].DATA, 'dossier', 'MANIFEST')

    def write_dossier(self):
        BMMuser, dcm, ga = user_ns['BMMuser'], user_ns['dcm'], user_ns['ga']
        if self.filename is None or self.start is None:
            print(error_msg('Filename and/or start number no given.'))
            return None
        firstfile = f'{self.filename}.{self.start:03d}'
        if not os.path.isfile(os.path.join(BMMuser.DATA, firstfile)):
            print(error_msg(f'Could not find {os.path.join(BMMuser.DATA, firstfile)}'))
            return None

        # figure out various filenames
        basename     = self.filename
        htmlfilename = os.path.join(BMMuser.DATA, 'dossier/', self.filename+'-01.html')
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

        print(f'writing {htmlfilename}')
        o = open(htmlfilename, 'w')

        # dossier header
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_top.tmpl')) as f:
            content = f.readlines()
        o.write(''.join(content).format(filename      = self.filename,
                                        date          = BMMuser.date,
                                        seqnumber     = seqnumber, ))

        # left sidebar, entry for XRF file in the case of fluorescence data
        thismode = plotting_mode(self.mode)
        if thismode == 'xs':
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
                content = f.readlines()
            o.write(''.join(content).format(basename      = basename,
                                            xrffile       = quote('../XRF/'+str(self.xrffile)),
                                            xrfuid        = self.xrfuid, ))

        # middle part of dossier
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_middle.tmpl')) as f:
            content = f.readlines()
        o.write(''.join(content).format(basename      = basename,
                                        scanlist      = self.scanlist,
                                        motors        = self.motors,
                                        sample        = self.sample,
                                        prep          = self.prep,
                                        comment       = self.comment,
                                        websnap       = quote('../snapshots/'+self.websnap),
                                        webuid        = self.webuid,
                                        anasnap       = quote('../snapshots/'+self.anasnap),
                                        anauid        = self.anauid,
                                        usb1snap      = quote('../snapshots/'+self.usb1snap),
                                        usb1uid       = self.usb1uid,
                                        usb2snap      = quote('../snapshots/'+self.usb2snap),
                                        usb2uid       = self.usb2uid, ))

        # middle part, XRF and glancing angle alignment images
        if thismode == 'xs':
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
                content = f.readlines()
            o.write(''.join(content).format(xrfsnap       = quote('../XRF/'+str(self.xrfsnap)),
                                            pccenergy     = '%.1f' % self.pccenergy,
                                            ocrs          = self.ocrs,
                                            rois          = self.rois,
                                            symbol        = self.element,))
            if BMMuser.instrument == 'glancing angle stage':
                with open(os.path.join(startup_dir, 'tmpl', 'dossier_ga.tmpl')) as f:
                    content = f.readlines()
                o.write(''.join(content).format(ga_align      = ga.alignment_filename,
                                                ga_yuid       = ga.y_uid,
                                                ga_puid       = ga.pitch_uid,
                                                ga_fuid       = ga.f_uid, ))
            
        # end of dossier
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_bottom.tmpl')) as f:
            content = f.readlines()
        o.write(''.join(content).format(e0            = '%.1f' % self.e0,
                                        edge          = self.edge,
                                        element       = f'{self.element} (<a href="https://en.wikipedia.org/wiki/{element_name(self.element)}">{element_name(self.element)}</a>, {Z_number(self.element)})',
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
                                        filename      = self.filename,))
            
        o.close()


        manifest = open(self.manifest_file, 'a')
        manifest.write(htmlfilename + '\n')
        manifest.close()
        self.write_manifest()

        if pngfilename is not None and os.path.isfile(pngfilename):
            try:
                img_to_slack(pngfilename)
            except:
                post_to_slack('failed to post image: {pngfilename}')
                pass

        return htmlfilename

    def write_manifest(self):
        '''Update the scan manifest and the corresponding static html file.'''
        BMMuser = user_ns['BMMuser']
        with open(self.manifest_file) as f:
            lines = [line.rstrip('\n') for line in f]

        experimentlist = ''
        for l in lines:
            if not os.path.isfile(l):
                continue
            this = os.path.basename(l)
            experimentlist += '<li><a href="./%s">%s</a></li>\n' % (this, this)

        with open(os.path.join(BMMuser.DATA, 'dossier', 'manifest.tmpl')) as f:
            content = f.readlines()
        indexfile = os.path.join(BMMuser.DATA, 'dossier', '00INDEX.html')
        o = open(indexfile, 'w')
        o.write(''.join(content).format(date           = BMMuser.date,
                                        experimentlist = experimentlist,))
        o.close()


    def make_merged_triplot(self, uidlist, filename, mode):
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
                        proj.add_group(this.group)
                        this.group.args['label'] = save
                        cnt += 1
                    except:
                        pass # presumably this is noisy data for which a valid background was not found
        except:
            pass # presumably this is noisy data for which a valid background was not found
        if cnt == 0:
            print(whisper(f'Unable to make triplot'))
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
        proj.save()
        print(whisper(f'Wrote Athena project to {projname}'))
