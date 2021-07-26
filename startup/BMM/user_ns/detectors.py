
import os, json
from BMM.functions import run_report
from BMM.user_ns.bmm import BMMuser
from ophyd import EpicsSignal

run_report(__file__, text='detectors and cameras')

##############################################################
# ______ _    _ _____ _      _    _____ ________  ___ _____  #
# |  _  \ |  | |  ___| |    | |  |_   _|_   _|  \/  ||  ___| #
# | | | | |  | | |__ | |    | |    | |   | | | .  . || |__   #
# | | | | |/\| |  __|| |    | |    | |   | | | |\/| ||  __|  #
# | |/ /\  /\  / |___| |____| |____| |  _| |_| |  | || |___  #
# |___/  \/  \/\____/\_____/\_____/\_/  \___/\_|  |_/\____/  #
##############################################################


run_report('\t'+'dwelltime')
with_quadem, with_struck, with_dualem, with_xspress3 = True, True, False, True
if with_xspress3 is True:
    BMMuser.readout_mode = 'xspress3'
from BMM.dwelltime import LockedDwellTimes

_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'

#abs_set(_locked_dwell_time, 0.5)


##########################################
#  _____ ___________ _   _ _____  _   __ #
# /  ___|_   _| ___ \ | | /  __ \| | / / #
# \ `--.  | | | |_/ / | | | /  \/| |/ /  #
#  `--. \ | | |    /| | | | |    |    \  #
# /\__/ / | | | |\ \| |_| | \__/\| |\  \ #
# \____/  \_/ \_| \_|\___/ \____/\_| \_/ #
##########################################
                                      
                                      

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

## electron yield detector, via Keithley and v2f converter
vor.channels.chan31.name = 'eyield'
vor.channels.chan31.kind = 'omitted'


bicron = GonioStruck('XF:06BM-ES:1{Sclr:1}', name='bicron')
for i in list(range(1,33)):
    text = 'bicron.channels.chan%d.kind = \'omitted\'' % i
    exec(text)
bicron.channels.chan25.kind = 'hinted'
bicron.channels.chan26.kind = 'hinted'
bicron.channels.chan25.name = 'Bicron'
bicron.channels.chan26.name = 'APD'


## if this startup file is "%run -i"-ed, then need to reset
## foils to the serialized configuration
jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
if os.path.isfile(jsonfile):
    user = json.load(open(jsonfile))
    if 'rois' in user:
        rois.set(user['rois'])
        BMMuser.read_rois = None
## else if starting bsui fresh, perform the delayed foil configuration
if BMMuser.read_rois is not None:
    rois.set(BMMuser.read_rois)
    BMMuser.read_rois = None


#######################################################################################
#  _____ _      _____ _____ ___________ ________  ___ _____ _____ ___________  _____  #
# |  ___| |    |  ___/  __ \_   _| ___ \  _  |  \/  ||  ___|_   _|  ___| ___ \/  ___| #
# | |__ | |    | |__ | /  \/ | | | |_/ / | | | .  . || |__   | | | |__ | |_/ /\ `--.  #
# |  __|| |    |  __|| |     | | |    /| | | | |\/| ||  __|  | | |  __||    /  `--. \ #
# | |___| |____| |___| \__/\ | | | |\ \\ \_/ / |  | || |___  | | | |___| |\ \ /\__/ / #
# \____/\_____/\____/ \____/ \_/ \_| \_|\___/\_|  |_/\____/  \_/ \____/\_| \_|\____/  #
#######################################################################################


run_report('\t'+'electrometers')
from BMM.electrometer import BMMQuadEM, BMMDualEM, dark_current

        
quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')

quadem1.I0.kind = 'hinted'
quadem1.It.kind = 'hinted'
quadem1.Ir.kind = 'hinted'
quadem1.Iy.kind = 'omitted'      # 'hinted'

quadem1.I0.name = 'I0'
quadem1.It.name = 'It'
quadem1.Ir.name = 'Ir'
quadem1.Iy.name = 'Iy'


## need to do something like this:
##    caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 7
## to get a sensible reporting precision from the Ix channels
def set_precision(pv, val):
    EpicsSignal(pv.pvname + ".PREC", name='').put(val)

set_precision(quadem1.current1.mean_value, 3)
toss = quadem1.I0.describe()
set_precision(quadem1.current2.mean_value, 3)
toss = quadem1.It.describe()
set_precision(quadem1.current3.mean_value, 3)
toss = quadem1.Ir.describe()
set_precision(quadem1.current4.mean_value, 3)
toss = quadem1.Iy.describe()


try:                            # not 100% guaranteed to be in place
    dualio = BMMDualEM('XF:06BM-BI{EM:3}EM180:', name='DualI0')
    dualio.Ia.kind = 'hinted'
    dualio.Ib.kind = 'hinted'
    dualio.Ia.name = 'Ia'
    dualio.Ib.name = 'Ib'
except:
    dualio = None


quadem2 = BMMQuadEM('XF:06BM-BI{EM:2}EM180:', name='quadem2')


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
from BMM.db import file_resource


## see 01-bmm.py for definition of nas_path
from BMM.user_ns.bmm import nas_path
xascam = BMMSnapshot(root=nas_path, which='XAS',    name='xascam')
xrdcam = BMMSnapshot(root=nas_path, which='XRD',    name='xrdcam')
anacam = BMMSnapshot(root=nas_path, which='analog', name='anacam')
anacam.device = '/dev/v4l/by-id/usb-MACROSIL_AV_TO_USB2.0-video-index0'
anacam.x, anacam.y = 640, 480    # width, height

econcam = BMMSnapshot(root=nas_path, which='econ', name='econcam')
econcam.device = '/dev/v4l/by-id/usb-e-con_systems_See3CAM_CU55_1CD90500-video-index0'
econcam.x, econcam.y = 1280, 720 # width, height
econcam.brightness = 50

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

    

###############################################
# ______ _____ _       ___ _____ _   _ _____  #
# | ___ \_   _| |     / _ \_   _| | | /  ___| #
# | |_/ / | | | |    / /_\ \| | | | | \ `--.  #
# |  __/  | | | |    |  _  || | | | | |`--. \ #
# | |    _| |_| |____| | | || | | |_| /\__/ / #
# \_|    \___/\_____/\_| |_/\_/  \___/\____/  #
###############################################
                                           

run_report('\t'+'Pilatus & prosilica')
from BMM.pilatus import MyDetector, PilatusGrabber

## prosilica3 = MyDetector('XF:06BM-BI{Scr:3}', name='Prosilica3')
## p3         = ImageGrabber(prosilica3)
pilatus = MyDetector('XF:06BMB-ES{Det:PIL100k}:', name='Pilatus')
pil     = PilatusGrabber(pilatus)



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
#config_ophyd_logging(file="xspress3_ophyd_debug.log", level=logging.DEBUG)

from BMM.xspress3_4element import BMMXspress3Detector_4Element
from BMM.xspress3_1element import BMMXspress3Detector_1Element
from nslsii.areadetector.xspress3 import build_detector_class 

xs = False
use_4element = True
if with_xspress3 is True:
    run_report('\t'+'4-element SDD with Xspress3')

    xs = BMMXspress3Detector_4Element(
        prefix='XF:06BM-ES{Xsp:1}:',
        name='xs',
        read_attrs=['hdf5']
    )

    # This is necessary for when the ioc restarts
    # we have to trigger one image for the hdf5 plugin to work correctly
    # else, we get file writing errors
    # DEBUGGING: commented this out
    xs.hdf5.warmup()

    # JOSH: proposed changes for new IOC
    #       as far as I can tell we need 'hinted' all the way down
    # Hints:
    xs.channels.kind = 'hinted'
    for channel in xs.iterate_channels():
        channel.kind = 'hinted'
        channel.mcarois.kind = 'hinted'
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'hinted'
    # # Hints:
    # for n in range(1,5):
    #     for m in range(1,17):
    #         r = getattr(xs, f'channel{n}').rois
    #         thisroi = getattr(r, 'roi{:02}'.format(m))
    #         thisroi.value.kind = 'hinted'
    #         #getattr(xs, f'channel{n}').rois.roi01.value.kind = 'hinted'
    #         #getattr(xs, f'channel{n}').rois.roi02.value.kind = 'hinted'
    #         #getattr(xs, f'channel{n}').rois.roi03.value.kind = 'hinted'
    #         #getattr(xs, f'channel{n}').rois.roi04.value.kind = 'hinted'

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

    # JOSH: proposed changes for new IOC
    for channel in xs.iterate_channels():
        mcaroi_names = list(channel.iterate_mcaroi_attr_names())
        channel.mcarois.read_attrs = mcaroi_names
        channel.mcarois.configuration_attrs = mcaroi_names
        for mcaroi in channel.iterate_mcarois():
            mcaroi.total_rbv.kind = 'omitted'

    # for n, d in xs.channels.items():
    #     roi_names = ['roi{:02}'.format(j) for j in range(1,17)]
    #     d.rois.read_attrs = roi_names
    #     d.rois.configuration_attrs = roi_names
    #     for roi_n in roi_names:
    #         getattr(d.rois, roi_n).value_sum.kind = 'omitted'

        xs.set_rois()
        #xrf = xs.measure_xrf

    # else:
    #     run_report('\t'+'1-element SDD with Xspress3')
    #     xs1 = BMMXspress3Detector_1Element('XF:06BM-ES{Xsp:1}:', name='xs1')
    #     xs1.hdf5.warmup()

    #     # JOSH: proposed changes for new IOC
    #     for mcaroi in xs1.channels.channel08.iterate_mcarois():
    #         mcaroi.total_rbv.kind = 'hinted'

    #     # for m in range(1,17):
    #     #     r = xs1.channel8.rois
    #     #     thisroi = getattr(r, 'roi{:02}'.format(m))
    #     #     thisroi.value.kind = 'hinted'
    #     xs1.settings.configuration_attrs = ['acquire_period',
    #                                         'acquire_time',
    #                                         'gain',
    #                                         'image_mode',
    #                                         'manufacturer',
    #                                         'model',
    #                                         'num_exposures',
    #                                         'num_images',
    #                                         'temperature',
    #                                         'temperature_actual',
    #                                         'trigger_mode',
    #                                         'config_path',
    #                                         'config_save_path',
    #                                         'invert_f0',
    #                                         'invert_veto',
    #                                         'xsp_name',
    #                                         'num_channels',
    #                                         'num_frames_config',
    #                                         'run_flags',
    #                                         'trigger_signal']

    #     # JOSH: proposed changes for new IOC
    #     mcaroi_names = list(xs1.channels.channel08.iterate_mcaroi_attr_names())
    #     xs1.channels.channel08.mcarois.read_attrs = mcaroi_names
    #     xs1.channels.channel08.mcarois.configuration_attrs = mcaroi_names
    #     for mcaroi in xs1.channels.channel08.iterate_mcarois():
    #         mcaroi.total_rbv.kind = 'omitted'
    #     xs1.set_rois()

    #     # #for n, d in xs1.channels.items():
    #     # roi_names = ['roi{:02}'.format(j) for j in range(1,17)]
    #     # xs1.channel8.rois.read_attrs = roi_names
    #     # xs1.channel8.rois.configuration_attrs = roi_names
    #     # for roi_n in roi_names:
    #     #    getattr(xs1.channel8.rois, roi_n).value_sum.kind = 'omitted'
    #     # xs1.set_rois()
    #     #xrf1 = xs1.measure_xrf

# JL turn off ophyd logging
import logging
config_ophyd_logging(level=logging.WARNING)

