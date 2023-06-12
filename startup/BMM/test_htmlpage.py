
import os
from BMM.dossier import BMMDossier


dossier = BMMDossier()

dossier.inifile       = os.path.join(BMMuser.folder, 'all_references.ini')
dossier.filename      = 'Mo-K-MolybdenumFoil'
dossier.start         = 1
dossier.end           = 5
dossier.experimenters = 'Darren Driscoll'
dossier.seqstart      = 'Monday, August 1, 2022 03:57 PM'
dossier.seqend        = 'Monday, August 1, 2022 04:03 PM'
dossier.e0            = 5964.3
dossier.edge          = 'L3'
dossier.element       = 'Pr'
dossier.scanlist      = None
dossier.sample        = 'Mo-K-MolybdenumFoil'
dossier.prep          = 'PEEK Cell 2mm'
dossier.comment       = 'Bruce is testing code, sorry for cluttering up your disk space'
dossier.mode          = 'fluorescence'
dossier.pccenergy     = 6084.2
dossier.bounds        = '-200.0 -30.0 -10.0 25 13k'
dossier.steps         = '10.0 2.0 0.5 0.05k'
dossier.times         = '0.5 0.5 0.5 0.5'
dossier.clargs        = ''
dossier.websnap       = '../snapshots/Mo-K-MolybdenumFoil_XASwebcam_2022-08-04T21-23-49.jpg'
dossier.webuid        = '93f5ddd2-8a97-4f78-ba4b-26620ea5e97e'
dossier.anasnap       = '../snapshots/Mo-K-MolybdenumFoil_analog_2022-08-04T21-23-49.jpg'
dossier.anauid        = '12b6c8c8-eac5-4011-a561-6d953435d73d'
dossier.usb1snap      = '../snapshots/Mo-K-MolybdenumFoil_usb1_2022-08-04T21-23-49.jpg'
dossier.usb1uid       = 'ca48ad21-326c-4e04-8400-30ef3252fa18'
dossier.usb2snap      = '../snapshots/Mo-K-MolybdenumFoil_usb2_2022-08-04T21-23-49.jpg'
dossier.usb2uid       = '6a97bb1c-d95b-4243-899f-44c5c89c7c9d'
dossier.xrfsnap       = ''
dossier.xrffile       = ''
dossier.xrfuid        = ''
dossier.ocrs          = ''
dossier.rois          = ''
dossier.htmlpage      = True
dossier.ththth        = False
dossier.initext       = None
dossier.uidlist       = ['1e5cfc4a-a739-4433-bf42-e1fb60af53aa']
dossier.url           = ''
dossier.doi           = ''
dossier.cif           = ''
dossier.instrument    = '' #ga.dossier_entry()
dossier.motors        = motor_sidebar()
