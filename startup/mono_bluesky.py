from bluesky_unreal import UnrealClient, UnrealSignal
client = UnrealClient()
client.get_all_properties()

bragg = UnrealSignal(preset_name="mono_remote", name='Bragg (Crystals)')
para = UnrealSignal(preset_name="mono_remote", name='Para (Crystals)')
perp = UnrealSignal(preset_name="mono_remote", name='Perp (Crystals)')

