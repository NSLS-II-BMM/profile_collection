
from BMM.dwelltime import LockedDwellTimes

run_report(__file__)


_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'

#abs_set(_locked_dwell_time, 0.5)


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
