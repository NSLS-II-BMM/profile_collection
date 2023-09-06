
import os, json
from BMM.functions import run_report, whisper
from BMM.user_ns.bmm import BMMuser
from ophyd import EpicsSignal
from ophyd.sim import noisy_det

run_report(__file__, text='detectors and cameras')

with_pilatus = False


##########################################
#  _____ ___________ _   _ _____  _   __ #
# /  ___|_   _| ___ \ | | /  __ \| | / / #
# \ `--.  | | | |_/ / | | | /  \/| |/ /  #
#  `--. \ | | |    /| | | | |    |    \  #
# /\__/ / | | | |\ \| |_| | \__/\| |\  \ #
# \____/  \_/ \_| \_|\___/ \____/\_| \_/ #
##########################################
                                      
## use of Struck is largely DEPRECATED.  Code remains in case there is
## ever a need to return to the analog signal chain for the SDD.  At
## this point (Sep 2023), it is no longer an easy switch between
## XSpress3 and analog.  Work will be required to get the analog
## solution fully integrated into data acquisition.
##
## that is work that would be greatly exacerbated by the fact that the
## only known way to visualize the XRF spectrum and the ROI settings
## involves the Canberra software on a Windows 95 machine using a
## security key fob.
##
## all that said, the only way (currently) of reading the XRD Bicron
## is to use the Struck

run_report('\t'+'Struck')
from BMM.struck import BMMVortex, GonioStruck, icrs, ocrs

vor = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vor')
icrs['XF:06BM-ES:1{Sclr:1}.S3']  = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S4']  = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S5']  = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S6']  = vor.channels.chan10

icrs['XF:06BM-ES:1{Sclr:1}.S15'] = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S16'] = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S17'] = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S18'] = vor.channels.chan10

icrs['XF:06BM-ES:1{Sclr:1}.S19'] = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S20'] = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S21'] = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S22'] = vor.channels.chan10

ocrs['XF:06BM-ES:1{Sclr:1}.S3']  = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S4']  = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S5']  = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S6']  = vor.channels.chan14

ocrs['XF:06BM-ES:1{Sclr:1}.S15'] = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S16'] = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S17'] = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S18'] = vor.channels.chan14

ocrs['XF:06BM-ES:1{Sclr:1}.S19'] = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S20'] = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S21'] = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S22'] = vor.channels.chan14

vor.set_hints(1)

for i in list(range(3,23)):
    text = 'vor.channels.chan%d.kind = \'normal\'' % i
    exec(text)
for i in list(range(1,3)) + list(range(23,33)):
    text = 'vor.channels.chan%d.kind = \'omitted\'' % i
    exec(text)

vor.state.kind = 'omitted'


vor.dtcorr1.name = 'DTC1'
vor.dtcorr2.name = 'DTC2'
vor.dtcorr3.name = 'DTC3'
vor.dtcorr4.name = 'DTC4'

vor.dtcorr21.name = 'DTC2_1'
vor.dtcorr22.name = 'DTC2_2'
vor.dtcorr23.name = 'DTC2_3'
vor.dtcorr24.name = 'DTC2_4'

vor.dtcorr31.name = 'DTC3_1'
vor.dtcorr32.name = 'DTC3_2'
vor.dtcorr33.name = 'DTC3_3'
vor.dtcorr34.name = 'DTC3_4'


vor.channels.chan3.name = 'ROI1'
vor.channels.chan4.name = 'ROI2'
vor.channels.chan5.name = 'ROI3'
vor.channels.chan6.name = 'ROI4'
vor.channels.chan7.name = 'ICR1'
vor.channels.chan8.name = 'ICR2'
vor.channels.chan9.name = 'ICR3'
vor.channels.chan10.name = 'ICR4'
vor.channels.chan11.name = 'OCR1'
vor.channels.chan12.name = 'OCR2'
vor.channels.chan13.name = 'OCR3'
vor.channels.chan14.name = 'OCR4'
vor.channels.chan15.name = 'ROI2_1'
vor.channels.chan16.name = 'ROI2_2'
vor.channels.chan17.name = 'ROI2_3'
vor.channels.chan18.name = 'ROI2_4'
vor.channels.chan19.name = 'ROI3_1'
vor.channels.chan20.name = 'ROI3_2'
vor.channels.chan21.name = 'ROI3_3'
vor.channels.chan22.name = 'ROI3_4'
vor.channels.chan25.name = 'Bicron'
vor.channels.chan26.name = 'APD'



bicron = GonioStruck('XF:06BM-ES:1{Sclr:1}', name='bicron')
for i in list(range(1,33)):
    text = 'bicron.channels.chan%d.kind = \'omitted\'' % i
    exec(text)
bicron.channels.chan25.kind = 'hinted'
bicron.channels.chan26.kind = 'hinted'
bicron.channels.chan25.name = 'Bicron'
bicron.channels.chan26.name = 'APD'



#######################################################################################
#  _____ _      _____ _____ ___________ ________  ___ _____ _____ ___________  _____  #
# |  ___| |    |  ___/  __ \_   _| ___ \  _  |  \/  ||  ___|_   _|  ___| ___ \/  ___| #
# | |__ | |    | |__ | /  \/ | | | |_/ / | | | .  . || |__   | | | |__ | |_/ /\ `--.  #
# |  __|| |    |  __|| |     | | |    /| | | | |\/| ||  __|  | | |  __||    /  `--. \ #
# | |___| |____| |___| \__/\ | | | |\ \\ \_/ / |  | || |___  | | | |___| |\ \ /\__/ / #
# \____/\_____/\____/ \____/ \_/ \_| \_|\___/\_|  |_/\____/  \_/ \____/\_| \_|\____/  #
#######################################################################################


run_report('\t'+'electrometer and ion chambers')
from BMM.electrometer import BMMQuadEM, BMMDualEM, dark_current, IntegratedIC

        
quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')
quadem1.enable_electrometer()
print(whisper('\t\t\t'+'instantiated quadem1'))
quadem1.I0.kind, quadem1.It.kind, quadem1.Ir.kind, quadem1.Iy.kind = 'omitted', 'hinted', 'hinted', 'omitted'
quadem1.I0.name, quadem1.It.name, quadem1.Ir.name, quadem1.Iy.name = 'I0q', 'It', 'Ir', 'Iy'


## need to do something like this:
##    caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 7
## to get a sensible reporting precision from the Ix channels
def set_precision(pv, val):
    EpicsSignal(pv.pvname + ".PREC", name='').put(val)

set_precision(quadem1.current1.mean_value, 3)
toss = quadem1.I0.describe()    # this seems to be necessary for the BEC to use the correct precision
set_precision(quadem1.current2.mean_value, 3)
toss = quadem1.It.describe()
set_precision(quadem1.current3.mean_value, 3)
toss = quadem1.Ir.describe()
set_precision(quadem1.current4.mean_value, 3)
toss = quadem1.Iy.describe()


# try:                            # might not be in use
#     dualio = BMMDualEM('XF:06BM-BI{EM:3}EM180:', name='DualI0')
#     dualio.Ia.kind = 'hinted'
#     dualio.Ib.kind = 'hinted'
#     dualio.Ia.name = 'Ia'
#     dualio.Ib.name = 'Ib'
# except:
#     dualio = None


try:                            # might not be in use
    ic0 = IntegratedIC('XF:06BM-BI{IC:0}EM180:', name='Ic0')
    ic0.enable_electrometer()
    print(whisper('\t\t\t'+'instantiated ic0'))
    ic0.Ia.kind = 'hinted'
    ic0.Ib.kind = 'omitted'
    ic0.Ia.name = 'I0'
    ic0.Ib.name = 'I0b'
    set_precision(ic0.current1.mean_value, 3)
    toss = ic0.Ia.describe()
    set_precision(ic0.current2.mean_value, 3)
    toss = ic0.Ib.describe()
except:    
    print(whisper('\t\t\t'+'ic0 is not available, falling back to ophyd.sim.noisy_det'))
    ic0 = noisy_det

try:                            # might not be in use
    ic1 = IntegratedIC('XF:06BM-BI{IC:1}EM180:', name='Ic1')
    ic1.enable_electrometer()
    print(whisper('\t\t\t'+'instantiated ic1'))
    ic1.Ia.kind = 'hinted'
    ic1.Ib.kind = 'hinted'
    ic1.Ia.name = 'Ita'
    ic1.Ib.name = 'Itb'
    set_precision(ic1.current1.mean_value, 3)
    toss = ic1.Ia.describe()
    set_precision(ic1.current2.mean_value, 3)
    toss = ic1.Ib.describe()
except:    
    print(whisper('\t\t\t'+'ic1 is not available, falling back to ophyd.sim.noisy_det'))
    ic1 = noisy_det

#set_precision(ic0.current1.mean_value, 3)
#toss = ic0.Ia.describe()
#set_precision(ic0.current2.mean_value, 3)
#toss = ic0.Ib.describe()
    
#quadem2 = BMMQuadEM('XF:06BM-BI{EM:2}EM180:', name='quadem2')


####################################################
#  _____   ___  ___  ___ ___________  ___   _____  #
# /  __ \ / _ \ |  \/  ||  ___| ___ \/ _ \ /  ___| #
# | /  \// /_\ \| .  . || |__ | |_/ / /_\ \\ `--.  #
# | |    |  _  || |\/| ||  __||    /|  _  | `--. \ #
# | \__/\| | | || |  | || |___| |\ \| | | |/\__/ / #
#  \____/\_| |_/\_|  |_/\____/\_| \_\_| |_/\____/  #
####################################################

run_report('\t'+'cameras')
from BMM.camera_device import BMMSnapshot, snap
from BMM.db import file_resource, show_snapshot


# this root location is deprecated for the camera devices.  the NAS devices were retired
# in early 2023. The _root of the camera device will be reset when the user configuration
# happens, so this initial configuration is harmless, if confusing
from BMM.user_ns.bmm import nas_path
xascam = BMMSnapshot(root=nas_path, which='XAS',    name='xascam')
xrdcam = BMMSnapshot(root=nas_path, which='XRD',    name='xrdcam')
anacam = BMMSnapshot(root=nas_path, which='analog', name='anacam')
anacam.device = '/dev/v4l/by-id/usb-MACROSIL_AV_TO_USB2.0-video-index0'
anacam.x, anacam.y = 640, 480    # width, height

from BMM.webcam_device import AxisWebcam
from BMM.handler import WEBCAM_JPEG_HANDLER
from BMM.user_ns.base import db
#db.reg.register_handler("BEAMLINE_WEBCAM", WEBCAM_JPEG_HANDLER)
base = os.path.join(BMMuser.folder, 'raw')
# testcam = AxisWebcam(base=base, address='xf06bm-cam6', name='XAS webcam')
# testcam.beamline_id = 'BMM (NSLS-II 06BM)'
# testcam.annotation_string = 'Welcome to BMM'

# econcam = BMMSnapshot(root=nas_path, which='econ', name='econcam')
# econcam.device = '/dev/v4l/by-id/usb-e-con_systems_See3CAM_CU55_1CD90500-video-index0'
# econcam.x, econcam.y = 1280, 720 # width, height
# econcam.brightness = 50

## the output file names is hidden away in the dict returned by this: a.describe()['args']['get_resources']()
#
# a=db.v2[-1] 
#
# BMM XRD.111 [8] ▶ a.describe()['args']['get_resources']()[0]['root']                                                                                  
# Out[8]: '/mnt/nfs/nas1/xf06bm/experiments/XAS/snapshots'
#
# BMM XRD.111 [9] ▶ a.describe()['args']['get_resources']()[0]['resource_path']                                                                         
# Out[9]: '17f7c1e0-6796-49da-95aa-c3f2ccc3d5ca_%d.jpg'

# img=db.v2[-1].primary.read()['anacam_image']
# this gives a 3D array, [480,640,3], where the 3 are RGB values 0-to-255
# how to export this as a jpg image???


from BMM.usb_camera import CAMERA
usb1 = CAMERA('XF:06BM-ES{UVC-Cam:1}', name='usb1')
usbcam1 = BMMSnapshot(root=nas_path, which='usb', name='usbcam1')
#usb1.image.shaped_image.kind = 'normal'

usb2 = CAMERA('XF:06BM-ES{UVC-Cam:2}', name='usb2')
usbcam2 = BMMSnapshot(root=nas_path, which='usb', name='usbcam2')

###############################################
# ______ _____ _       ___ _____ _   _ _____  #
# | ___ \_   _| |     / _ \_   _| | | /  ___| #
# | |_/ / | | | |    / /_\ \| | | | | \ `--.  #
# |  __/  | | | |    |  _  || | | | | |`--. \ #
# | |    _| |_| |____| | | || | | |_| /\__/ / #
# \_|    \___/\_____/\_| |_/\_/  \___/\____/  #
###############################################
                                           

if with_pilatus is True:
    run_report('\t'+'Pilatus & prosilica')
    from BMM.pilatus import MyDetector #, PilatusGrabber

    ## prosilica3 = MyDetector('XF:06BM-BI{Scr:3}', name='Prosilica3')
    ## p3         = ImageGrabber(prosilica3)
    pilatus = MyDetector('XF:06BMB-ES{Det:PIL100k}:', name='Pilatus')
    #pil     = PilatusGrabber(pilatus)
    pilatus.autoincrement.put(1)


#######################################################
# __   __ _________________ _____ _____ _____  _____  #
# \ \ / //  ___| ___ \ ___ \  ___/  ___/  ___||____ | #
#  \ V / \ `--.| |_/ / |_/ / |__ \ `--.\ `--.     / / #
#  /   \  `--. \  __/|    /|  __| `--. \`--. \    \ \ #
# / /^\ \/\__/ / |   | |\ \| |___/\__/ /\__/ /.___/ / #
# \/   \/\____/\_|   \_| \_\____/\____/\____/ \____/  #
#######################################################

# JL: debugging xspress3 IOC crash
from ophyd.log import config_ophyd_logging
import logging
config_ophyd_logging(file="xspress3_ophyd_debug.log", level=logging.DEBUG)


xs = False
xs1 = False
from BMM.user_ns.dwelltime import with_xspress3, use_4element, use_1element
if with_xspress3 is True and use_4element is True:
    run_report('\t'+'4-element SDD with Xspress3')
    from BMM.xspress3_4element import BMMXspress3Detector_4Element
    #from BMM.xspress3_1element import BMMXspress3Detector_1Element
    #from nslsii.areadetector.xspress3 import build_detector_class 
    #from nslsii.areadetector.xspress3 import build_xspress3_class 

    xs = BMMXspress3Detector_4Element(
        prefix='XF:06BM-ES{Xsp:1}:',
        name='4-element SDD',
        read_attrs=['hdf5']
    )
    a = xs.hdf5.run_time.get()
    
    # This is necessary for when the ioc restarts
    # we have to trigger one image for the hdf5 plugin to work correctly
    # else, we get file writing errors
    # DEBUGGING: commented this out
    if xs.hdf5.run_time.get() == 0.0:
        xs.hdf5.warmup()

    # Hints:
    #xs.channels.kind = 'hinted'
    for channel in xs.iterate_channels():
        channel.kind = 'hinted'
        #channel.mcarois.kind = 'hinted'
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'hinted'

    xs.cam.configuration_attrs = ['acquire_period',
                                  'acquire_time',
                                  # JOSH: change for new IOC
                                   #       gain is no longer a PV?
                                   # 'gain',
                                   'image_mode',
                                   'manufacturer',
                                   'model',
                                   'num_exposures',
                                   'num_images',
                                   'temperature',
                                   'temperature_actual',
                                   'trigger_mode',
                                   'config_path',
                                   'config_save_path',
                                   'invert_f0',
                                   'invert_veto',
                                   'xsp_name',
                                   'num_channels',
                                   'num_frames_config',
                                   'run_flags',
                                   'trigger_signal']

    for channel in xs.iterate_channels():
        mcaroi_names = list(channel.iterate_mcaroi_attr_names())
        #channel.mcarois.read_attrs = mcaroi_names
        #channel.mcarois.configuration_attrs = mcaroi_names
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'omitted'

    xs.set_rois()
    hdf5folder = os.path.join('/nsls2', 'data', 'bmm', 'assets', 'xspress3', *BMMuser.date.split('-'))
    xs.hdf5.read_path_template = hdf5folder
    xs.hdf5.write_path_template = hdf5folder
    xs.hdf5.file_path.put(hdf5folder)

    try:
        xs.channel01.xrf.dtype_str = "<f8"
        xs.channel02.xrf.dtype_str = "<f8"
        xs.channel03.xrf.dtype_str = "<f8"
        xs.channel04.xrf.dtype_str = "<f8"
        xs.channel01.get_external_file_ref().dtype_str = "<f8"
        xs.channel02.get_external_file_ref().dtype_str = "<f8"
        xs.channel03.get_external_file_ref().dtype_str = "<f8"
        xs.channel04.get_external_file_ref().dtype_str = "<f8"
    except:
        pass
        
    ## this stage_sigs and trigger business was needed with the new (as of January 2023)
    ## to maintain the correct triggering state for our mode of operation here at BMM
    ## apparently to serve the needs of other BLs, the triggering mode would default
    ## back to "Software" at the end of a scan.  This overrides that behavior.
    xs.cam.stage_sigs[xs.cam.trigger_mode] = "Internal"

if with_xspress3 is True and use_1element is True:
    run_report('\t'+'1-element SDD with Xspress3')
    from BMM.xspress3_1element import BMMXspress3Detector_1Element
    #from nslsii.areadetector.xspress3 import build_detector_class 
    #from nslsii.areadetector.xspress3 import build_xspress3_class 

    xs1 = BMMXspress3Detector_1Element(
        prefix='XF:06BM-ES{Xsp:1}:',
        name='1-element SDD',
        read_attrs=['hdf5']
    )

    # This is necessary for when the ioc restarts
    # we have to trigger one image for the hdf5 plugin to work correctly
    # else, we get file writing errors
    # DEBUGGING: commented this out
    #xs1.hdf5.warmup()

    # Hints:
    #xs1.channels.kind = 'hinted'
    for channel in xs1.iterate_channels():
        channel.kind = 'hinted'
        #channel.mcarois.kind = 'hinted'
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'hinted'

    xs1.cam.configuration_attrs = ['acquire_period',
                                   'acquire_time',
                                   'image_mode',
                                   'manufacturer',
                                   'model',
                                   'num_exposures',
                                   'num_images',
                                   'temperature',
                                   'temperature_actual',
                                   'trigger_mode',
                                   'config_path',
                                   'config_save_path',
                                   'invert_f0',
                                   'invert_veto',
                                   'xsp_name',
                                   'num_channels',
                                   'num_frames_config',
                                   'run_flags',
                                   'trigger_signal']

    for channel in xs1.iterate_channels():
        mcaroi_names = list(channel.iterate_mcaroi_attr_names())
        #channel.mcarois.read_attrs = mcaroi_names
        #channel.mcarois.configuration_attrs = mcaroi_names
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'omitted'

    xs1.set_rois()
    hdf5folder = os.path.join('/nsls2', 'data', 'bmm', 'assets', 'xspress3', *BMMuser.date.split('-'))
    xs1.hdf5.read_path_template = hdf5folder
    xs1.hdf5.write_path_template = hdf5folder
    xs1.hdf5.file_path.put(hdf5folder)
    xs1.cam.stage_sigs[xs.cam.trigger_mode] = "Internal"




        
def set_xs_folder():
    hdf5folder = os.path.join('/nsls2', 'data', 'bmm', 'assets', 'xspress3', *BMMuser.date.split('-'))
    xs.hdf5.read_path_template = hdf5folder
    xs.hdf5.write_path_template = hdf5folder
    xs.hdf5.file_path.put(hdf5folder)


