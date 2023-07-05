from ophyd import Device, Signal, Component
from bluesky_unreal import UnrealSignal, UnrealPositioner

class A(Device):
    sig = Component(Signal, name='sig', kind="hinted")
    bragg = Component(UnrealSignal, name="bragg", preset_name='mono_remote',
                                    kind="hinted")
    para = Component(UnrealPositioner, name="para", preset_name='mono_remote',
                                    kind="hinted")


a = A(name='dcm')