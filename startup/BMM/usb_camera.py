    
from pathlib import PurePath

from nslsii.ad33 import SingleTriggerV33
from ophyd import Component as C
from ophyd.areadetector import AreaDetector, ImagePlugin
from ophyd.areadetector.filestore_mixins import (
    FileStorePluginBase,
)
from ophyd.areadetector.filestore_mixins import resource_factory, FileStoreIterativeWrite, FileStorePluginBase
from itertools import count
from ophyd.areadetector.plugins import JPEGPlugin_V33

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)
md = user_ns["RE"].md


class BMMFileStoreJPEG(FileStorePluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = "BMM_USBCAM"  # spec name stored in resource doc
        self.stage_sigs.update(
            [
                ("file_template", "%s%s_%6.6d.jpeg"),
                ("file_write_mode", "Single"),
            ]
        )
        # 'Single' file_write_mode means one image : one file.
        # It does NOT mean that 'num_images' is ignored.
        self._point_counter = None

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()

    def _generate_resource(self, resource_kwargs):
        resource, self._datum_factory = resource_factory(
            spec=self.filestore_spec,
            root=str(self.reg_root),
            resource_path=self._fn + "_%6.6d.jpeg",
            resource_kwargs=resource_kwargs,
            path_semantics=self.path_semantics,
        )

        # If a Registry is set, we need to allow it to generate the uid for us.
        # this code path will eventually be removed
        if self._reg is not None:
            # register_resource has accidentally different parameter names...
            self._resource_uid = self._reg.register_resource(
                rpath=resource["resource_path"],
                rkwargs=resource["resource_kwargs"],
                root=resource["root"],
                spec=resource["spec"],
                path_semantics=resource["path_semantics"],
            )
            resource["uid"] = self._resource_uid
        # If a Registry is not set, we need to generate the uid.

        self._resource_uid = resource["uid"]

        self._asset_docs_cache.append(("resource", resource))

    def generate_datum(self, key, timestamp, datum_kwargs):
        i = next(self._point_counter)
        datum_kwargs = datum_kwargs or {}
        datum_kwargs.update({"point_number": i})
        return super().generate_datum(key, timestamp, datum_kwargs)

    def stage(self):
        super().stage()
        # # this over-rides the behavior is the base stage
        self._fn = self._fp + self.file_name.get()
        res_path = self._fn + "_%6.6d.jpeg"

        # resource_kwargs = {
        #     "filename": self.file_name.get(),
        #     "frame_per_point": self.get_frames_per_point(),
        # }
        self._generate_resource({})
        self._point_counter = count()

    def unstage(self):
        self._point_counter = None
        super().unstage()



class BMMJPEGPlugin(JPEGPlugin_V33, BMMFileStoreJPEG):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_paths()

    def _update_paths(self):
        self.reg_root = self.root_path_str
        self._write_path_template = self.root_path_str + "%Y/%m/%d/"
        self._read_path_template = self.root_path_str + "%Y/%m/%d/"


    @property
    def root_path_str(self):
        root_path = f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/{self.parent.name}/"
        return root_path

    
    def stage(self, *args, **kwargs):
        self._update_paths()
        super().stage(*args, **kwargs)


class BMMUVC(AreaDetector):
    image = C(ImagePlugin, "image1:")
    jpeg = C(
        BMMJPEGPlugin,
        "JPEG1:",
        write_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/usbcam/%Y/%m/%d/",
        read_path_template=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/usbcam/%Y/%m/%d/",
        read_attrs=[],
        root=f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/usbcam/",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.cam.trigger_mode, "Internal")])


    def make_data_key(self):
        source = "PV:{}".format(self.prefix)
        # This shape is expected to match arr.shape for the array.
        shape = (
            self.cam.array_size.array_size_y.get(),
            self.cam.array_size.array_size_x.get(),
            3,  # Always save in color
        )
        chunks = (
            1,  # Only save one image
            self.cam.array_size.array_size_y.get(),
            self.cam.array_size.array_size_x.get(),
            3,  # Always save in color   
        )
        return dict(
            shape=shape,
            chunks=chunks,
            source=source,
            dtype="array",
            dtype_str="|u1",
            external="FILESTORE:",
        )


class BMMUVCSingleTrigger(SingleTriggerV33, BMMUVC):

    pass
