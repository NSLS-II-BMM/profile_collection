
import os, json
from BMM.functions import run_report, whisper
from BMM.user_ns.base import RE
from BMM.user_ns.bmm import BMMuser
from ophyd import EpicsSignal
from ophyd.sim import noisy_det

run_report(__file__, text='detectors and cameras')

with_pilatus = False
with_cam1 = True
with_cam2 = True

from ophyd.scaler import EpicsScaler

class GonioStruck(EpicsScaler):
    def on(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def on_plan(self):
        yield from mv(self.state, 1)

    def off_plan(self):
        yield from mv(self.state, 0)


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

# It is important that the /name/ of the signal being used for I0 be 'I0',
# the signal for It be 'It', and Ir be 'Ir'.  That allows the kafka
# consumer and other Tiled clients to correctly interpret the columns of the
# data table.
#
# omitted signals should get names related to what they /could/ be, but are
# distinct from the main signal names.

run_report('\t'+'electrometer and ion chambers')
from BMM.electrometer import BMMQuadEM, BMMDualEM, dark_current, IntegratedIC

ION_CHAMBERS = []

# configure signal chains for I0/It/Ir, configuration flags from BMM.user_ns.dwelltime
from BMM.user_ns.dwelltime import with_ic0, with_ic1, with_ic2, with_iy
        
quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')
quadem1.enable_electrometer()
print(whisper('\t\t\t'+'instantiated quadem1'))
if with_ic0 is False:
    quadem1.I0.kind, quadem1.I0.name = 'hinted', 'I0'
else:
    quadem1.I0.kind, quadem1.I0.name = 'omitted', 'I0q'

if with_ic1 is False:
    quadem1.It.kind, quadem1.It.name = 'hinted', 'It'
else:
    quadem1.It.kind, quadem1.It.name = 'omitted', 'Itq'

if with_ic2 is False:
    quadem1.Ir.kind, quadem1.Ir.name = 'hinted', 'Ir'
else:
    quadem1.Ir.kind, quadem1.Ir.name = 'omitted', 'Irq'

quadem1.Iy.kind, quadem1.Iy.name = 'omitted', 'Iy'

if with_iy is True:
    ION_CHAMBERS.append(quadem1)
    quadem1.Iy.kind, quadem1.Iy.name = 'hinted', 'Iy'

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


#######################################################################
## A note about PV nomenclature for the ion chambers:
##
## The prefixes are:
##   I0: XF:06BM-BI{IC:0}EM180:
##   It: XF:06BM-BI{IC:1}EM180:
##   Ir: XF:06BM-BI{IC:3}EM180:
##
## That's right, 2 got skipped. This was an error in provisioning the
## ion chambers.  It was easier to configure bsui correctly than
## to fix the functioning ion chamber.
#######################################################################

try:                            # might not be in use
    ic0 = IntegratedIC('XF:06BM-BI{IC:0}EM180:', name='Ic0')
    ic0.enable_electrometer()
    print(whisper('\t\t\t'+'instantiated ic0'))
    if with_ic0 is False:
        ic0.Ia.kind, ic0.Ia.name = 'omitted', 'I0a'
    else:
        ic0.Ia.kind, ic0.Ia.name = 'hinted', 'I0'
        
    ic0.Ib.kind, ic0.Ib.name = 'omitted', 'I0b'
    set_precision(ic0.current1.mean_value, 3)
    toss = ic0.Ia.describe()
    set_precision(ic0.current2.mean_value, 3)
    toss = ic0.Ib.describe()
    ION_CHAMBERS.append(ic0)
except Exception as E:
    print(E)
    print(whisper('\t\t\t'+'ic0 is not available, falling back to ophyd.sim.noisy_det'))
    ic0 = noisy_det

try:                            # might not be in use
    ic1 = IntegratedIC('XF:06BM-BI{IC:1}EM180:', name='Ic1')
    ic1.enable_electrometer()
    print(whisper('\t\t\t'+'instantiated ic1'))
    if with_ic1 is False:
        ic1.Ia.kind, ic1.Ia.name = 'omitted', 'Ita'
    else:
        ic1.Ia.kind, ic1.Ia.name = 'hinted', 'It'
    ic1.Ib.kind, ic1.Ib.name = 'omitted', 'Itb'
    set_precision(ic1.current1.mean_value, 3)
    toss = ic1.Ia.describe()
    set_precision(ic1.current2.mean_value, 3)
    toss = ic1.Ib.describe()
    ION_CHAMBERS.append(ic1)
except:    
    print(whisper('\t\t\t'+'ic1 is not available, falling back to ophyd.sim.noisy_det'))
    ic1 = noisy_det


try:                            # might not be in use
    ic2 = IntegratedIC('XF:06BM-BI{IC:3}EM180:', name='Ic2')
    ic2.enable_electrometer()
    print(whisper('\t\t\t'+'instantiated ic2'))
    if with_ic2 is False:
        ic2.Ia.kind, ic2.Ia.name = 'omitted', 'Ira'
    else:
        ic2.Ia.kind, ic2.Ia.name = 'hinted', 'Ir'
    ic2.Ib.kind, ic2.Ib.name = 'omitted', 'Irb'
    set_precision(ic2.current1.mean_value, 3)
    toss = ic2.Ia.describe()
    set_precision(ic2.current2.mean_value, 3)
    toss = ic2.Ib.describe()
    #ION_CHAMBERS.append(ic2)
except:    
    print(whisper('\t\t\t'+'ic2 is not available, falling back to ophyd.sim.noisy_det'))
    ic2 = noisy_det


    
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
from BMM.camera_device import BMMSnapshot, snap, AxisCaprotoCam
from BMM.db import file_resource, show_snapshot


# this root location is deprecated for the camera devices.  The _root
# of the camera device will be reset when the user configuration
# happens, so this initial configuration is harmless and transitory
run_report('\t\t'+'caproto IOCs for webcams')
temp_root = '/nsls2/data3/bmm/XAS/bucket'
xascam = AxisCaprotoCam("XF:06BM-ES{AxisCaproto:6}:", name="webcam-1",
                        root_dir=f"/nsls2/data3/bmm/proposals/{RE.md['cycle']}/{RE.md['data_session']}/assets")
xrdcam = AxisCaprotoCam("XF:06BM-ES{AxisCaproto:5}:", name="webcam-2",
                        root_dir=f"/nsls2/data3/bmm/proposals/{RE.md['cycle']}/{RE.md['data_session']}/assets")
run_report('\t\t'+'initializing analog camera')
anacam = BMMSnapshot(root=temp_root, which='analog', name='anacam')
anacam.image.shape = (480, 640, 3)
anacam.device = '/dev/v4l/by-id/usb-MACROSIL_AV_TO_USB2.0-video-index0'
anacam.x, anacam.y = 640, 480    # width, height



run_report('\t\t'+'USB cameras')


from BMM.usb_camera import BMMUVCSingleTrigger
if with_cam1 is True:
    usb1 = BMMUVCSingleTrigger('XF:06BM-ES{UVC-Cam:1}', name="usbcam-1", read_attrs=["jpeg"])
else:
    usb1, usbcam1 = None, None

if with_cam2 is True:
    usb2 = BMMUVCSingleTrigger('XF:06BM-ES{UVC-Cam:2}', name="usbcam-2", read_attrs=["jpeg"])
else:
    usb2, usbcam2 = None, None



def display_last_image_usb_cam(catalog, camera=usb1):
    from PIL import Image
    print(catalog[-1]['primary']['data'][f'{camera.name}_image'])

    Image.fromarray(
        catalog[-1]['primary']['data'][f'{camera.name}_image'].read()[0]
    ).show()


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
#config_ophyd_logging(file="xspress3_ophyd_debug.log", level=logging.DEBUG)


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


