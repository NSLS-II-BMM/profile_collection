from ophyd.positioner import SoftPositioner
from bluesky_unreal import UnrealClient

class UnrealPositioner(SoftPositioner):

    def __init__(self, *args, preset_name, server_address='http://localhost:30010', **kwargs):

        self._client = UnrealClient(server_address)
        self._preset_name = preset_name
        init_pos = self._client.get_value(self._preset_name, self.name)
        super().__init__(*args, init_pos=initial_value, **kwargs)


    def _setup_move(self, position, status):
      self._client.set_value(self._preset_name, self.name, position)
      super()._setup_move(self)


#bragg = UnrealPositioner(preset_name="NewRemoteControlPreset", name='motor1')