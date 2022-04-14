
import os
from BMM.dossier import BMMDossier


dossier = BMMDossier()

dossier.inifile       = os.path.join(BMMuser.folder, 'scan.ini')
dossier.filename      = 'Pttest'
dossier.start         = 4
dossier.end           = 4
dossier.experimenters = 'Bruce Ravel'
dossier.seqstart      = 'Wednesday, October 20, 2021 03:57 PM'
dossier.seqend        = 'Wednesday, October 20, 2021 04:03 PM'
dossier.e0            = 11563.8
dossier.edge          = 'L3'
dossier.element       = 'Pt'
dossier.scanlist      = None
dossier.sample        = 'Pt foil'
dossier.prep          = 'Pt foil standard'
dossier.comment       = 'Welcome to BMM'
dossier.mode          = 'transmission'
dossier.pccenergy     = 11726.0
dossier.bounds        = '-200.0 -30.0 -10.0 15.5 12k'
dossier.steps         = '10.0 2.0 0.5 0.05k'
dossier.times         = '0.5 0.5 0.5 0.5'
dossier.clargs        = ''
dossier.websnap       = '../snapshots/Pttest_XASwebcam_2021-10-20T15-57-34.jpg'
dossier.webuid        = '7493d2a0-0ce0-49c4-a2dc-dba1c3a8e0f1'
dossier.anasnap       = '../snapshots/Pttest_analog_2021-10-20T15-57-34.jpg'
dossier.anauid        = 'f39fe9a5-1c5c-4502-b64b-d9fedefb1d36'
dossier.usb1snap      = '../snapshots/Pttest_usb1_2021-10-20T15-57-34.jpg'
dossier.usb1uid       = 'ae526013-29cc-42c8-968a-f0f13f63c7a5'
dossier.usb2snap      = '../snapshots/Pttest_usb2_2021-10-20T15-57-34.jpg'
dossier.usb2uid       = 'b4b080c-a1b9-4349-8de2-decdfd27bed6'
dossier.xrfsnap       = ''
dossier.xrffile       = ''
dossier.xrfuid        = ''
dossier.ocrs          = ''
dossier.rois          = ''
dossier.htmlpage      = True
dossier.ththth        = False
dossier.initext       = None
dossier.uidlist       = ['62af0101-f2ce-4266-889f-e22e0480c841',]
dossier.url           = ''
dossier.doi           = ''
dossier.cif           = ''
dossier.instrument    = '' #ga.dossier_entry()
