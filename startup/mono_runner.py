from numpy import pi, sin, cos, arcsin
from bluesky_unreal import UnrealClient, UnrealSignal

HBARC      = 1973.270533241973

def motor_positions(energy, offset=30,twod=2*3.1351860):
        wavelength = 2*pi*HBARC / energy
        angle = arcsin(wavelength / twod)
        bragg = 180 * arcsin(wavelength/ twod) / pi
        para  = offset / (2*sin(angle))
        perp  = offset / (2*cos(angle))        
        return(bragg, para, perp)

bragg = UnrealSignal(preset_name="mono_remote", name='Bragg (Crystals)')
para = UnrealSignal(preset_name="mono_remote", name='Para (Crystals)')
perp = UnrealSignal(preset_name="mono_remote", name='Perp (Crystals)')
color = UnrealSignal(preset_name="mono_remote", name='Bragg (Laser_Emitter)')


bragg_pos,para_pos,perp_pos=motor_positions(4000)
bragg.set(bragg_pos)
para.set(para_pos)
perp.set(perp_pos)
color.set(bragg_pos)

print(f"bragg:{bragg_pos},para:{para_pos}, perp:{perp_pos}")
print("unreal",bragg.read(),para.read(),perp.read())
      