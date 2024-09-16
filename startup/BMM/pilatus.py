    
from pathlib import PurePath
from itertools import count

from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd.areadetector import AreaDetector, ImagePlugin
from ophyd.areadetector.cam import PilatusDetectorCam
from ophyd.areadetector.base import EpicsSignalWithRBV
from ophyd.areadetector.filestore_mixins import resource_factory, FileStoreHDF5, FileStoreTIFF, FileStoreIterativeWrite, FileStorePluginBase
from ophyd.areadetector.plugins import HDF5Plugin_V33, TIFFPlugin_V33, StatsPlugin_V33

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)
md = user_ns["RE"].md

from nslsii.ad33 import SingleTriggerV33
from ophyd import Component as C



######################################################################################
# ______ _____ _       ___ _____ _   _ _____              ___   _____________ _____  #
# | ___ \_   _| |     / _ \_   _| | | /  ___|            / / | | |  _  \  ___|  ___| #
# | |_/ / | | | |    / /_\ \| | | | | \ `--.  __      __/ /| |_| | | | | |_  |___ \  #
# |  __/  | | | |    |  _  || | | | | |`--. \ \ \ /\ / / / |  _  | | | |  _|     \ \ #
# | |    _| |_| |____| | | || | | |_| /\__/ /  \ V  V / /  | | | | |/ /| |   /\__/ / #
# \_|    \___/\_____/\_| |_/\_/  \___/\____/    \_/\_/_/   \_| |_/___/ \_|   \____/  #
######################################################################################
                                                                                  
                                                                                


class BMMFileStoreHDF5(FileStorePluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = "AD_HDF5"  # spec name stored in resource doc
        self.stage_sigs.update(
            [
                ("file_template", "%s%s_%6.6d.h5"),
                ("file_write_mode", "Capture"),
                ("capture", 1),
                # TODO: Remove once num capture is updated elsewhere
                #("num_capture", 3)

            ]
        )
        # 'Single' file_write_mode means one image : one file.
        # It does NOT mean that 'num_images' is ignored.

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()

    def stage(self):
        super().stage()
        # this over-rides the behavior from the base stage
        self._fn = self.file_template.get() % (
            self.file_path.get(),
            self.file_name.get(),
            # file_number is *next* iteration
            self.file_number.get(),
        )

        resource_kwargs = {
            "frame_per_point": self.get_frames_per_point(),
        }
        self._generate_resource(resource_kwargs)
    
class BMMHDF5Plugin(HDF5Plugin_V33, BMMFileStoreHDF5, FileStoreIterativeWrite):
    pass




class BMMPilatus(AreaDetector):
    image = C(ImagePlugin, "image1:")
    hdf5 = C(
        BMMHDF5Plugin,
        "HDF1:",
        write_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1/%Y/%m/%d/",
        read_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1//%Y/%m/%d/",
        read_attrs=[],
        root=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1/",
    )
    stats = C(EpicsSignalRO, "Stats1:Total_RBV")

    cam_file_path      = C(EpicsSignalWithRBV, 'cam1:FilePath')
    cam_file_name      = C(EpicsSignalWithRBV, 'cam1:FileName')
    cam_file_number    = C(EpicsSignalWithRBV, 'cam1:FileNumber')
    cam_auto_increment = C(EpicsSignalWithRBV, 'cam1:AutoIncrement')
    cam_file_template  = C(EpicsSignalWithRBV, 'cam1:FileTemplate')
    cam_full_file_name = C(EpicsSignalRO,      'cam1:FullFileName_RBV')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.stage_sigs.update([(self.cam.trigger_mode, "Internal")])

    def make_data_key(self):
        source = "PV:{}".format(self.prefix)
        # This shape is expected to match arr.shape for the array.
        shape = (
            1,
            self.cam.array_size.array_size_y.get(),
            self.cam.array_size.array_size_x.get(),
        )
        
        data_key = dict(
            shape=shape,
            source=source,
            dtype="array",
            dtype_str="<f4",
            external="FILESTORE:",
        )
        #print(data_key)
        return data_key


class BMMPilatusSingleTrigger(SingleTriggerV33, BMMPilatus):
    pass






######################################################################################
# ______ _____ _       ___ _____ _   _ _____              _______ _________________  #
# | ___ \_   _| |     / _ \_   _| | | /  ___|            / /_   _|_   _|  ___|  ___| #
# | |_/ / | | | |    / /_\ \| | | | | \ `--.  __      __/ /  | |   | | | |_  | |_    #
# |  __/  | | | |    |  _  || | | | | |`--. \ \ \ /\ / / /   | |   | | |  _| |  _|   #
# | |    _| |_| |____| | | || | | |_| /\__/ /  \ V  V / /    | |  _| |_| |   | |     #
# \_|    \___/\_____/\_| |_/\_/  \___/\____/    \_/\_/_/     \_/  \___/\_|   \_|     #
######################################################################################
                                                                                


class BMMFileStoreTIFF(FileStorePluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = "AD_TIFF"  # spec name stored in resource doc
        self.stage_sigs.update(
            [
                ("file_template", "%s%s_%6.6d.tiff"),
                ("file_write_mode", "Capture"),
                ("capture", 1),
                # TODO: Remove once num capture is updated elsewhere
                #("num_capture", 3)

            ]
        )
        # 'Single' file_write_mode means one image : one file.
        # It does NOT mean that 'num_images' is ignored.

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()

    def stage(self):
        super().stage()
        # this over-rides the behavior from the base stage
        self._fn = self.file_template.get() % (
            self.file_path.get(),
            self.file_name.get(),
            # file_number is *next* iteration
            self.file_number.get(),
        )

        resource_kwargs = {
            #"template": "%s%s_%6.6d.tiff",
            #"filename": self.file_name.get(),
            "frame_per_point": self.get_frames_per_point(),
            #"chunk_size": 1,
        }
        self._generate_resource(resource_kwargs)
    
class BMMTIFFPlugin(TIFFPlugin_V33, BMMFileStoreTIFF, FileStoreIterativeWrite):
    pass




class BMMPilatusTIFF(AreaDetector):
    image = C(ImagePlugin, "image1:")
    tiff = C(
        BMMTIFFPlugin,
        "TIFF1:",
        write_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1/%Y/%m/%d/",
        read_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1//%Y/%m/%d/",
        read_attrs=[],
        root=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/pilatus100k-1/",
    )
    stats = C(EpicsSignalRO, "Stats1:Total_RBV")

    cam_file_path      = C(EpicsSignalWithRBV, 'cam1:FilePath')
    cam_file_name      = C(EpicsSignalWithRBV, 'cam1:FileName')
    cam_file_number    = C(EpicsSignalWithRBV, 'cam1:FileNumber')
    cam_auto_increment = C(EpicsSignalWithRBV, 'cam1:AutoIncrement')
    cam_file_template  = C(EpicsSignalWithRBV, 'cam1:FileTemplate')
    cam_full_file_name = C(EpicsSignalRO,      'cam1:FullFileName_RBV')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.stage_sigs.update([(self.cam.trigger_mode, "Internal")])

    def make_data_key(self):
        source = "PV:{}".format(self.prefix)
        # This shape is expected to match arr.shape for the array.
        shape = (
            self.cam.array_size.array_size_y.get(),
            self.cam.array_size.array_size_x.get(),
        )
        
        data_key = dict(
            shape=shape,
            source=source,
            dtype="array",
            dtype_str="<f4",
            external="FILESTORE:",
        )
        #print(data_key)
        return data_key


class BMMPilatusTIFFSingleTrigger(SingleTriggerV33, BMMPilatusTIFF):
    pass


