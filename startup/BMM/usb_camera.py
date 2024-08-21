
# from ophyd import SingleTrigger, AreaDetector, DetectorBase, Component as Cpt, Device
# from ophyd import EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin
# from ophyd import DeviceStatus, Signal, Kind

# from ophyd.areadetector.plugins import ImagePlugin_V33, JPEGPlugin_V33
# from ophyd.areadetector.filestore_mixins import resource_factory, FileStoreIterativeWrite, FileStorePluginBase
# from ophyd.sim import new_uid
# from collections import deque
# from event_model import compose_stream_resource, StreamRange
# from pathlib import Path

# import time
# from PIL import Image, ImageFont, ImageDraw 
# import numpy as np
# from BMM.camera_device import annotate_image
# from BMM.functions import now
# import sys, datetime, uuid, itertools

# from ophyd.areadetector.base import NDDerivedSignal
# from ophyd.areadetector.filestore_mixins import resource_factory

# from BMM import user_ns as user_ns_module
# user_ns = vars(user_ns_module)
# md = user_ns["RE"].md



# # class ExternalFileReference(Signal):
# #     """
# #     A pure software Signal that describe()s an image in an external file.
# #     """

# #     def describe(self):
# #         resource_document_data = super().describe()
# #         resource_document_data[self.name].update(
# #             {
# #                 "external": "FILESTORE:",
# #                 "dtype": "array",
# #             }
# #         )
# #         return resource_document_data




# class FileStoreJPEG(FileStorePluginBase):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.filestore_spec = "BMM_USBCAM"  # spec name stored in resource doc
#         self.stage_sigs.update(
#             [
#                 #("file_template", "%s%s_%6.6d.jpeg"),
#                 ("file_write_mode", "Single"),
#             ]
#         )
#         # 'Single' file_write_mode means one image : one file.
#         # It does NOT mean that 'num_images' is ignored.

#     def describe(self):
#         ret = super().describe()
#         key = self.name
#         color_mode = self.parent.cam.color_mode.get(as_string=True)
#         if not ret:
#             ret = {key: {}}
#         ret[key].update({
#             "shape": [
#                 # self.parent.cam.num_images.get(),
#                 3,  # number of channels (RGB)
#                 self.array_size.depth.get(),  # should be width, need a PR in the relevant AD repo?
#                 self.array_size.height.get(),
#             ],
#             "dtype": "array",
#             "source": self.parent.name,
#             "external": "STREAM:",
#         })

#         cam_dtype = self.parent.cam.data_type.get(as_string=True)
#         type_map = {'UInt8': '|u1', 'UInt16': '<u2', 'Float32':'<f4', "Float64":'<f8'}
#         if cam_dtype in type_map:
#             ret[key].setdefault('dtype_str', type_map[cam_dtype])

#         return ret

#     def stage(self):
#         ret = super().stage()
#         # this over-rides the behavior is the base stage
#         # self._fn = self._fp

#         full_file_name = self.full_file_name.get()  # TODO: .replace("_000.jpg", "_%d.jpg")

#         self._stream_resource_document, self._stream_datum_factory = compose_stream_resource(
#             data_key=self.name,
#             # For event-model<1.21.0:
#             # spec=self.filestore_spec,
#             # root="/",
#             # resource_path=full_file_name,
#             # resource_kwargs={"resource_path": full_file_name},
#             # For event-model>=1.21.0:
#             mimetype="image/jpeg",
#             uri=uri,
#             parameters={},
#         )
#         print(self._stream_resource_document)

#         self._asset_docs_cache.append(
#             ("stream_resource", self._stream_resource_document)
#         )

#         # resource_kwargs = {
#         #     "resource_path": resource_path
#         # }
#         # self._generate_resource(resource_kwargs)
#         # self._asset_docs_cache[0][1].pop("resource_path")  # Temporary fix to avoid collision with the kwarg in 'BMM_JPEG_HANDLER'.
#         return ret

#     def generate_datum(self, *args, **kwargs):
#         stream_datum_document = self._stream_datum_factory(
#             StreamRange(start=0, stop=1),
#         )
#         self._asset_docs_cache.append(("stream_datum", stream_datum_document))
#         return ""

#     def collect_asset_docs(self):
#         """The method to collect resource/datum documents."""
#         items = list(self._asset_docs_cache)
#         self._asset_docs_cache.clear()
#         yield from items


# class FileStoreJPEG2:
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._asset_docs_cache = []
#         self._counter = None
#         self._datum_factory = None

#     def stage(self):
#         self._asset_docs_cache.clear()
#         self._counter = itertools.count()
#         full_file_name = self.full_file_name.get()  #.replace("_000.jpg", "_%3.3d.jpg")
#         print(f"{full_file_name = }")
#         resource, self._datum_factory = resource_factory(
#             "BMM_USBCAM",
#             "/",
#             full_file_name,
#             {},
#             "posix",
#         )
#         self._asset_docs_cache.append(("resource", resource))
#         return super().stage()




# class JPEGPluginWithFileStore(FileStoreJPEG2, JPEGPlugin_V33):
#     """Add this as a component to detectors that write JPEGs."""
#     pass


# # class StandardCameraWithJPEG(AreaDetector):
# #     jpeg = Cpt(JPEGPluginWithFileStore,
# #                suffix='JPEG1:',
# #                write_path_template=f'/nsls2/data3/bmm/proposal/{md["cycle"]}/{md["data_session"]}assets/usbcam-1/%Y/%m/%d/',
# #                root=f'/nsls2/data3/bmm/proposal/{md["cycle"]}/{md["data_session"]}/assets')



# # class JPEGPluginEnsuredOn(JPEGPluginWithFileStore):
# #     """Add this as a component to detectors that do not write JPEGs."""
# #     def __init__(self, *args, **kwargs):
# #         super().__init__(*args, **kwargs)
# #         # self.stage_sigs.update([('auto_save', 'No')])


# class CAMERA(SingleTrigger, AreaDetector): #SingleTrigger, Device, AreaDetector
#     image = Cpt(ImagePlugin, 'image1:')
#     jpeg1 = Cpt(JPEGPluginWithFileStore,# 'JPEG1:')
#                 suffix='JPEG1:',
#                 )
#                 # write_path_template=f'/nsls2/data3/bmm/proposals/{md["cycle"]}/{md["data_session"]}/assets/usbcam-1',
#                 # root=f'/nsls2/data3/bmm/proposals/{md["cycle"]}/{md["data_session"]}/assets')

#     jpeg_filepath = Cpt(EpicsSignal, 'JPEG1:FilePath')
#     jpeg_filetemplate = Cpt(EpicsSignal, 'JPEG1:FileTemplate')
#     jpeg_filename = Cpt(EpicsSignal, 'JPEG1:FileName')
#     jpeg_autoincrement = Cpt(EpicsSignal, 'JPEG1:AutoIncrement')
#     jpeg_fileformat = Cpt(EpicsSignal, 'JPEG1:FileTemplate')
#     jpeg_writefile = Cpt(EpicsSignal, 'JPEG1:WriteFile')
#     jpeg_create_dir_depth = Cpt(EpicsSignal, 'JPEG1:CreateDirectory')
#     jpeg_autosave = Cpt(EpicsSignal, 'JPEG1:AutoSave')

#     def __init__(self, *args, root_dir=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.stage_sigs.update(
#             [
#                 ("cam.image_mode", "Single"),
#             ]
#         )
#         self.kind = Kind.normal
#         self.jpeg1.kind = Kind.normal
#         if root_dir is None:
#             msg = "The 'root_dir' kwarg cannot be None"
#             raise RuntimeError(msg)
#         self._root_dir = root_dir
#         # self._resource_document, self._datum_factory = None, None
#         # self._asset_docs_cache = deque()

#         # self._SPEC = "BMM_USBCAM"
#         #self.image.name = self.name

#     def _update_paths(self):
#         self._root_dir = self.root_path_str

#     @property
#     def root_path_str(self):
#         root_path = f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/"
#         return root_path


#     def trigger(self):
#         i = next(self.jpeg1._counter)
#         if i > 0:
#             assert "Bruce said this could never happen. - Dan Allan, 2024"
#         datum = self.jpeg1._datum_factory({"index": i})
#         self.jpeg1._asset_docs_cache.append(("datum", datum))
#         self._datum_id = datum["datum_id"]
#         ret = super().trigger()
#         return ret

#     def collect_asset_docs(self):
#         yield from self.jpeg1._asset_docs_cache
#         self.jpeg1._asset_docs_cache.clear()

#     def stage(self):
#         self.jpeg1.auto_save.put(1)
#         assets_dir = self.name
#         data_file_no_ext = f"{self.name}_{new_uid()}"
#         data_file_with_ext = f"{data_file_no_ext}.jpeg"


#       # Update AD IOC parameters:
#         self.jpeg_filepath.put(str(Path(self._root_dir) / Path(assets_dir)))
#         self.jpeg_filename.put(data_file_with_ext)
#         super().stage()
#         #self.ioc_stage.put(1)

#     def describe(self):
#         res = super().describe()
#         # if self.name == 'usbcam-1':
#         #     res[self.image.name].update(
#         #         {"shape": (1080, 1920), "dtype_str": "<f4"}
#         #     )
#         # elif self.name == 'usbcam-2':
#         #     res[self.image.name].update(
#         #         {"shape": (600, 800), "dtype_str": "<f4"}
#         #     )
#         res[f"{self.name}_jpeg1"] = {
#             "shape": (1080, 1920, 3),
#             "chunks": (1, 1080, 1920, 3,),
#             "dtype_str": "<f4",
#             "dtype": "array",
#             "source": "...",
#             "external": "FILESTORE:",
#         }
#         return res

#     def read(self):
#         res = super().read()
#         res[f"{self.name}_jpeg1"] = {"value": self._datum_id, "timestamp": time.time()}
#         return res

#     def unstage(self):
#         # self._resource_document = None
#         # self._datum_factory = None
#         #self.ioc_stage.put(0)

#         ## turn off file saving and return the camera to continuous mode for viewing
#         super().unstage()
#         self.jpeg1.auto_save.put(0)
#         self.cam.image_mode.put(2)
#         self.cam.acquire.put(1)

#     def stop(self, success=False):
#         self.jpeg1.auto_save.put(0)
#         return super().stop(success=success)

        
    # def _update_paths(self):
    #     self.jpeg_filepath.put(f"/nsls2/data3/bmm/proposals/{md['cycle']}/{md['data_session']}/assets/{self.name}/{datetime.datetime.now().strftime('%Y/%m/%d')}")


    # def collect_asset_docs(self):
    #     """The method to collect resource/datum documents."""
    #     items = list(self._asset_docs_cache)
    #     self._asset_docs_cache.clear()
    #     yield from items

    # def stage(self, *args, **kwargs):
    #     self._update_paths()
    #     self.jpeg_filename.put(str(uuid.uuid4()))
    #     # self._rel_path_template = f"{self.jpeg_filename.get()}_%d.jpg"
    #     # self._root = self.jpeg_filepath.get()
    #     # resource, self._datum_factory = resource_factory(
    #     #     self._SPEC, self._root, self._rel_path_template, {}, "posix")
    #     # self._asset_docs_cache.append(('resource', resource))
    #     self._counter = itertools.count()
        
    #     super().stage(*args, **kwargs)
    #     # # Clear asset docs cache which may have some documents from the previous failed run.
    #     # self._asset_docs_cache.clear()

    #     # self._resource_document, self._datum_factory, _ = compose_resource(
    #     #     start={"uid": "needed for compose_resource() but will be discarded"},
    #     #     spec="BMM_JPEG_HANDLER",
    #     #     root=self._root_dir,
    #     #     resource_path=str(Path(assets_dir) / Path(data_file_with_ext)),
    #     #     resource_kwargs={},
    #     # )
    
from pathlib import PurePath

from nslsii.ad33 import SingleTriggerV33
from ophyd import Component as C
from ophyd.areadetector import AreaDetector, ImagePlugin
from ophyd.areadetector.filestore_mixins import (
    FileStorePluginBase,
)
from itertools import count
from ophyd.areadetector.plugins import JPEGPlugin_V33


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
        datum_kwargs.update({"index": i})
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
            1, # Only save one image
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
