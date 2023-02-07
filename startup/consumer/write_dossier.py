import os
from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter
from urllib.parse import quote
from BMM.periodictable import Z_number, edge_energy, element_name
from dossier_tools import motor_sidebar, xrf_metadata, describe_mode

def get_user_text(md, thing):
    try:
        return md['start']['XDI']['_user'][thing]
    except:
        return f'sample text ({thing})'

def element_text(el):
    if Z_number(el) is None:
        return ''
    else:
        thistext  = f'{el} '
        thistext += f'(<a href="https://en.wikipedia.org/wiki/{element_name(el)}">'
        thistext += f'{element_name(el)}</a>, '
        thistext += f'{Z_number(el)})'
        return thistext

    
def image_exists(md, which):
    if '_snapshots' not in md['start']['XDI']:
        return False
    if which == 'ana':
        if 'anacam_uid' in md['start']['XDI']['_snapshots']:
            return True
    elif which == 'usb1':
        if 'usbcam1_uid' in md['start']['XDI']['_snapshots']:
            return True
    elif which == 'usb2':
        if 'usbcam2_uid' in md['start']['XDI']['_snapshots']:
            return True
    elif which == 'web':
        if 'webcam_uid' in md['start']['XDI']['_snapshots']:
            return True
    elif which == 'xrf_':
        if 'xrf_uid' in md['start']['XDI']['_snapshots']:
            return True
    return False

        
def xafs_dossier(catalog, uid):
    record = catalog[uid]
    modestuff = describe_mode(catalog, uid)


    
    ## this is temporary
    startup_dir = '/home/xf06bm/.ipython/profile_collection/startup'
    DATA = os.path.split(record.metadata['start']['XDI']['_snapshots']['analog_file'])[0]
    DATA = os.path.split(DATA)[0]
    
    seqnumber = 1

    
    filename = record.metadata['start']['XDI']['_filename']
    htmlfilename = os.path.join(DATA, 'dossier/', filename+'-01.html')
    basename = filename
    if os.path.isfile(htmlfilename):
        seqnumber = 2
        while os.path.isfile(os.path.join(DATA, 'dossier', "%s-%2.2d.html" % (filename,seqnumber))):
            seqnumber += 1
        basename     = "%s-%2.2d" % (filename,seqnumber)
        htmlfilename = os.path.join(DATA, 'dossier', "%s-%2.2d.html" % (filename,seqnumber))

    
    # dossier header
    with open(os.path.join(startup_dir, 'tmpl', 'dossier_top.tmpl')) as f:
        content = f.readlines()
    thiscontent = ''.join(content).format(measurement   = 'XAFS',
                                          filename      = record.metadata['start']['XDI']['_filename'],
                                          date          = get_user_text(record.metadata, 'date'),
                                          seqnumber     = seqnumber, )

    # left sidebar, entry for XRF file in the case of fluorescence data
    if image_exists(record.metadata, 'xrf'):
        xrfstuff = xrf_metadata(catalog, record.metadata['start']['XDI']['_snapshots']['xrf_uid'])
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_file.tmpl')) as f:
            content = f.readlines()
        xrfname = os.path.split(record.metadata['start']['XDI']['_snapshots']['xrf_image'])[1]
        xrfname = xrfname.replace('.png', '.xrf').replace('_XRF_', '_')
        thiscontent += ''.join(content).format(basename      = basename,
                                               xrffile       = quote(f'../XRF/{xrf_name}'),
                                               xrfuid        = record.metadata['start']['XDI']['_snapshots']['xrf_uid'], )

    # middle part of dossier
    instrument = ''
    if instrument == '':
        instrument = '<div id=boxinst><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p></div>'
    with open(os.path.join(startup_dir, 'tmpl', 'dossier_middle.tmpl')) as f:
        content = f.readlines()

    ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
    ## generate left sidebar text for the static html page for this scan sequence
    fname = "%s.%3.3d" % (filename, seqnumber)
    js_text = f'<a href="javascript:void(0)" onclick="toggle_visibility(\'{fname}\');" title="This is the scan number for {fname}, click to show/hide its UID">#{record.metadata["start"]["scan_id"]}</a><div id="{fname}" style="display:none;"><small>{uid}</small></div>'
    ## actually need to accumulate for the whole list 
    printedname = fname
    if len(fname) > 11:
        printedname = fname[0:6] + '&middot;&middot;&middot;' + fname[-5:]
    scanlist = f'<li><a href="../{quote(fname)}" title="Click to see the text of {fname}">{printedname}</a>&nbsp;&nbsp;&nbsp;&nbsp;{js_text}</li>\n' 


    instrument = get_user_text(record.metadata, 'instrument')
    if instrument.startswith('sample') is True:
        instrument = '<div id=boxinst><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p><p> &nbsp;</p></div>'
    
    thiscontent += ''.join(content).format(basename      = basename,
                                           scanlist      = scanlist,
                                           motors        = motor_sidebar(catalog, uid),
                                           sample        = get_user_text(record.metadata, 'sample'),
                                           prep          = get_user_text(record.metadata, 'prep'),
                                           comment       = get_user_text(record.metadata, 'comment'),
                                           instrument    = instrument)

    # middle part, cameras, one at a time and only if actually snapped
    if image_exists(record.metadata, 'web'):
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
            content = f.readlines()
        thisname = os.path.split(record.metadata['start']['XDI']['_snapshots']['webcam_file'])[1]
        thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+thisname),
                                               uid         = record.metadata['start']['XDI']['_snapshots']['webcam_uid'],
                                               camera      = 'webcam',
                                               description = 'XAS web camera', )
    if image_exists(record.metadata, 'ana'):
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
            content = f.readlines()
        thisname = os.path.split(record.metadata['start']['XDI']['_snapshots']['analog_file'])[1]
        thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+thisname),
                                               uid         = record.metadata['start']['XDI']['_snapshots']['anacam_uid'],
                                               camera      = 'anacam',
                                               description = 'analog pinhole camera', )
    if image_exists(record.metadata, 'usb1'):
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
            content = f.readlines()
        thisname = os.path.split(record.metadata['start']['XDI']['_snapshots']['usb1_file'])[1]
        thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+thisname),
                                               uid         = record.metadata['start']['XDI']['_snapshots']['usbcam1_uid'],
                                               camera      = 'usb1cam',
                                               description = 'USB camera #1', )
    if image_exists(record.metadata, 'usb2'):
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_img.tmpl')) as f:
            content = f.readlines()
        thisname = os.path.split(record.metadata['start']['XDI']['_snapshots']['usb2_file'])[1]
        thiscontent += ''.join(content).format(snap        = quote('../snapshots/'+thisname),
                                               uid         = record.metadata['start']['XDI']['_snapshots']['usbcam2_uid'],
                                               camera      = 'usb2cam',
                                               description = 'USB camera #2', )

    # middle part, XRF and glancing angle alignment images
    if image_exists(record.metadata, 'xrf'):
        with open(os.path.join(startup_dir, 'tmpl', 'dossier_xrf_image.tmpl')) as f:
            content = f.readlines()
        thisname = os.path.split(record.metadata['start']['XDI']['_snapshots']['xrf_image'])[1]
        thiscontent += ''.join(content).format(xrfsnap       = quote('../XRF/'+thisname),
                                               pccenergy     = xrfstuff['pccenergy'],
                                               ocrs          = xrfstuff['ocrs'],
                                               rois          = xrfstuff['rois'],
                                               symbol        = xrfstuff['symbol'],)
        if 'glancing' in BMMuser.instrument:
            with open(os.path.join(startup_dir, 'tmpl', 'dossier_ga.tmpl')) as f:
                content = f.readlines()
            thiscontent += ''.join(content).format(ga_align      = ga.alignment_filename,
                                                   ga_yuid       = ga.y_uid,
                                                   ga_puid       = ga.pitch_uid,
                                                   ga_fuid       = ga.f_uid, )

    # end of dossier
    e0 = edge_energy(record.metadata['start']['XDI']['Element']['symbol'],
                     record.metadata['start']['XDI']['Element']['edge'])
    try:
        pccenergy = record['start']['XDI']['_pccenergy']
    except:
        pccenergy = e0 + 300

    with open(os.path.join(startup_dir, 'tmpl', 'dossier_bottom.tmpl')) as f:
        content = f.readlines()
    thiscontent += ''.join(content).format(e0            = '%.1f' % e0 ,
                                           edge          = get_user_text(record.metadata, 'edge'),
                                           element       = element_text(record.metadata['start']['XDI']['Element']['symbol']),
                                           mode          = get_user_text(record.metadata, 'mode'),
                                           bounds        = get_user_text(record.metadata, 'bounds'),
                                           steps         = get_user_text(record.metadata, 'steps'),
                                           times         = get_user_text(record.metadata, 'times'),
                                           seqstart      = get_user_text(record.metadata, 'seqstart'), #self.seqstart,
                                           seqend        = get_user_text(record.metadata, 'seqend'), #self.seqend,
                                           mono          = modestuff['mono'],
                                           pdsmode       = f'{modestuff["mode"]} ({modestuff["mode_description"]})',
                                           pccenergy     = '%.1f' % pccenergy,
                                           experimenters = get_user_text(record.metadata, 'experimenters'),
                                           gup           = record.metadata['start']['XDI']['Facility']['GUP'],
                                           saf           = record.metadata['start']['XDI']['Facility']['SAF'],
                                           url           = '...',
                                           doi           = '...',
                                           cif           = '...',
                                           initext       = get_user_text(record.metadata, 'initext'), #highlight(self.initext, IniLexer(), HtmlFormatter()),
                                           clargs        = get_user_text(record.metadata, 'clargs'), #highlight(self.clargs, PythonLexer(), HtmlFormatter()),
                                           filename      = filename,)

    with open(htmlfilename, 'a') as o:
        o.write(thiscontent)

    print(f'wrote {htmlfilename}')

    # manifest = open(self.manifest_file, 'a')
    # manifest.write(f'xafs␣{htmlfilename}\n')
    # manifest.close()
    # self.write_manifest()

    # if pngfilename is not None and os.path.isfile(pngfilename):
    #     try:
    #         img_to_slack(pngfilename)
    #     except:
    #         post_to_slack(f'failed to post image: {pngfilename}')
    #         pass

    # return htmlfilename
