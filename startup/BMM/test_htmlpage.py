
import os
from BMM.dossier import BMMDossier


dossier = BMMDossier()

dossier.inifile       = os.path.join(BMMuser.folder, 'scan.ini')
dossier.filename      = 'Fe2O3'
dossier.start         = 1
dossier.end           = 1
dossier.experimenters = 'Bruce Ravel'
dossier.seqstart      = 'Monday, August 1, 2022 03:57 PM'
dossier.seqend        = 'Monday, August 1, 2022 04:03 PM'
dossier.e0            = 7112
dossier.edge          = 'K'
dossier.element       = 'Fe'
dossier.scanlist      = None
dossier.sample        = 'Fe2O3, hematite'
dossier.prep          = 'powder on tape'
dossier.comment       = 'from iron standards wheel'
dossier.mode          = 'transmission'
dossier.pccenergy     = 7412
dossier.bounds        = '-200.0 -30.0 -10.0 25 13k'
dossier.steps         = '10.0 2.0 0.5 0.05k'
dossier.times         = '0.5 0.5 0.5 0.5'
dossier.clargs        = ''
dossier.websnap       = '../snapshots/Fe2O3_XASwebcam_2022-08-01T10-23-38.jpg'
dossier.webuid        = 'f2046a74-b2a9-4238-b5d7-c6a1d6360adf'
dossier.anasnap       = '../snapshots/Fe2O3_analog_2022-08-01T10-23-38.jpg'
dossier.anauid        = '279232a1-a200-418f-82d5-752ac6170b4b'
dossier.usb1snap      = '../snapshots/Fe2O3_usb1_2022-08-01T10-23-38.jpg'
dossier.usb1uid       = '34f7a858-9619-418d-b021-d4fd2910ad7f'
dossier.usb2snap      = '../snapshots/Fe2O3_usb2_2022-08-01T10-23-38.jpg'
dossier.usb2uid       = 'ce29c763-0e1d-4634-a162-c50ae6e2231c'
dossier.xrfsnap       = ''
dossier.xrffile       = ''
dossier.xrfuid        = ''
dossier.ocrs          = ''
dossier.rois          = ''
dossier.htmlpage      = True
dossier.ththth        = False
dossier.initext       = None
dossier.uidlist       = ['5b9cc970-fa58-4708-81a5-ff64c54d9a4b',]
dossier.url           = ''
dossier.doi           = ''
dossier.cif           = ''
dossier.instrument    = '' #ga.dossier_entry()
