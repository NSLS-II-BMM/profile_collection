from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)
import time

run_report(__file__)

class FMBOEpicsMotor(EpicsMotor):
    resolution = Cpt(EpicsSignal, '.MRES')
    encoder = Cpt(EpicsSignal, '.REP')

    status_list = ('MTACT', 'MLIM', 'PLIM', 'AMPEN', 'LOOPM', 'TIACT', 'INTMO',
                   'DWPRO', 'DAERR', 'DVZER', 'ABDEC', 'UWPEN', 'UWSEN', 'ERRTAG',
                   'SWPOC', 'ASSCS', 'FRPOS', 'HSRCH', 'SODPL', 'SOPL', 'HOCPL',
                   'PHSRA', 'PREFE', 'TRMOV', 'IFFE', 'AMFAE', 'AMFE', 'FAFOE',
                   'WFOER', 'INPOS')

    ###################################################################
    # this is the complete list of status signals defined in the FMBO #
    # IOC for thier MCS8 motor controllers                            #
    ###################################################################
    mtact      = Cpt(EpicsSignal, '_MTACT_STS')
    mtact_desc = Cpt(EpicsSignal, '_MTACT_STS.DESC')
    mlim       = Cpt(EpicsSignal, '_MLIM_STS')
    mlim_desc  = Cpt(EpicsSignal, '_MLIM_STS.DESC')
    plim       = Cpt(EpicsSignal, '_PLIM_STS')
    plim_desc  = Cpt(EpicsSignal, '_PLIM_STS.DESC')
    ampen      = Cpt(EpicsSignal, '_AMPEN_STS')
    ampen_desc = Cpt(EpicsSignal, '_AMPEN_STS.DESC')
    loopm      = Cpt(EpicsSignal, '_LOOPM_STS')
    loopm_desc = Cpt(EpicsSignal, '_LOOPM_STS.DESC')
    tiact      = Cpt(EpicsSignal, '_TIACT_STS')
    tiact_desc = Cpt(EpicsSignal, '_TIACT_STS.DESC')
    intmo      = Cpt(EpicsSignal, '_INTMO_STS')
    intmo_desc = Cpt(EpicsSignal, '_INTMO_STS.DESC')
    dwpro      = Cpt(EpicsSignal, '_DWPRO_STS')
    dwpro_desc = Cpt(EpicsSignal, '_DWPRO_STS.DESC')
    daerr      = Cpt(EpicsSignal, '_DAERR_STS')
    daerr_desc = Cpt(EpicsSignal, '_DAERR_STS.DESC')
    dvzer      = Cpt(EpicsSignal, '_DVZER_STS')
    dvzer_desc = Cpt(EpicsSignal, '_DVZER_STS.DESC')
    abdec      = Cpt(EpicsSignal, '_ABDEC_STS')
    abdec_desc = Cpt(EpicsSignal, '_ABDEC_STS.DESC')
    uwpen      = Cpt(EpicsSignal, '_UWPEN_STS')
    uwpen_desc = Cpt(EpicsSignal, '_UWPEN_STS.DESC')
    uwsen      = Cpt(EpicsSignal, '_UWSEN_STS')
    uwsen_desc = Cpt(EpicsSignal, '_UWSEN_STS.DESC')
    errtg      = Cpt(EpicsSignal, '_ERRTG_STS')
    errtg_desc = Cpt(EpicsSignal, '_ERRTG_STS.DESC')
    swpoc      = Cpt(EpicsSignal, '_SWPOC_STS')
    swpoc_desc = Cpt(EpicsSignal, '_SWPOC_STS.DESC')
    asscs      = Cpt(EpicsSignal, '_ASSCS_STS')
    asscs_desc = Cpt(EpicsSignal, '_ASSCS_STS.DESC')
    frpos      = Cpt(EpicsSignal, '_FRPOS_STS')
    frpos_desc = Cpt(EpicsSignal, '_FRPOS_STS.DESC')
    hsrch      = Cpt(EpicsSignal, '_HSRCH_STS')
    hsrch_desc = Cpt(EpicsSignal, '_HSRCH_STS.DESC')
    sodpl      = Cpt(EpicsSignal, '_SODPL_STS')
    sodpl_desc = Cpt(EpicsSignal, '_SODPL_STS.DESC')
    sopl       = Cpt(EpicsSignal, '_SOPL_STS')
    sopl_desc  = Cpt(EpicsSignal, '_SOPL_STS.DESC')
    hocpl      = Cpt(EpicsSignal, '_HOCPL_STS')
    hocpl_desc = Cpt(EpicsSignal, '_HOCPL_STS.DESC')
    phsra      = Cpt(EpicsSignal, '_PHSRA_STS')
    phsra_desc = Cpt(EpicsSignal, '_PHSRA_STS.DESC')
    prefe      = Cpt(EpicsSignal, '_PREFE_STS')
    prefe_desc = Cpt(EpicsSignal, '_PREFE_STS.DESC')
    trmov      = Cpt(EpicsSignal, '_TRMOV_STS')
    trmov_desc = Cpt(EpicsSignal, '_TRMOV_STS.DESC')
    iffe       = Cpt(EpicsSignal, '_IFFE_STS')
    iffe_desc  = Cpt(EpicsSignal, '_IFFE_STS.DESC')
    amfae      = Cpt(EpicsSignal, '_AMFAE_STS')
    amfae_desc = Cpt(EpicsSignal, '_AMFAE_STS.DESC')
    amfe       = Cpt(EpicsSignal, '_AMFE_STS')
    amfe_desc  = Cpt(EpicsSignal, '_AMFE_STS.DESC')
    fafoe      = Cpt(EpicsSignal, '_FAFOE_STS')
    fafoe_desc = Cpt(EpicsSignal, '_FAFOE_STS.DESC')
    wfoer      = Cpt(EpicsSignal, '_WFOER_STS')
    wfoer_desc = Cpt(EpicsSignal, '_WFOER_STS.DESC')
    inpos      = Cpt(EpicsSignal, '_INPOS_STS')
    inpos_desc = Cpt(EpicsSignal, '_INPOS_STS.DESC')

    def status(self):
        text = '\n  %s is %s\n\n' % (self.name, self.prefix)
        for signal in self.read_attrs:
            if signal.upper() not in self.status_list:
                continue
            suffix = getattr(self, signal).pvname.replace(self.prefix, '')
            text += '  %-26s : %-19s  %s   %s \n' % (getattr(self, signal+'_desc').value,
                                                     getattr(self, signal).enum_strs[getattr(self, signal).value],
                                                     bold_msg(getattr(self, signal).value),
                                                     whisper(suffix))
        boxedtext('%s status signals' % self.name, text, 'green')
    
    def wh(self):
        return(round(self.user_readback.value, 3))

class XAFSEpicsMotor(FMBOEpicsMotor):
    hlm = Cpt(EpicsSignal, '.HLM', kind='config')
    llm = Cpt(EpicsSignal, '.LLM', kind='config')
    kill_cmd = Cpt(EpicsSignal, '_KILL_CMD.PROC')

    #def wh(self):
    #    return(round(self.user_readback.value, 3))

    
class EndStationEpicsMotor(EpicsMotor):
    hlm = Cpt(EpicsSignal, '.HLM', kind='config')
    llm = Cpt(EpicsSignal, '.LLM', kind='config')
    kill_cmd = Cpt(EpicsSignal, ':KILL')

    def wh(self):
        return(round(self.user_readback.value, 3))


class VacuumEpicsMotor(FMBOEpicsMotor):
    hlm = Cpt(EpicsSignal, '.HLM', kind='config')
    llm = Cpt(EpicsSignal, '.LLM', kind='config')
    kill_cmd = Cpt(EpicsSignal, '_KILL_CMD.PROC')

    #def wh(self):
    #    return(round(self.user_readback.value, 3))

    # def _setup_move(self, *args):
    #     self.kill_cmd.put(1)
    #     super()._setup_move(*args)
        
    
    def _done_moving(self, *args, **kwargs):
        ## this method is originally defined as Positioner, a base class of EpicsMotor
        ## tack on instructions for killing the motor after movement
        super()._done_moving(*args, **kwargs)
        time.sleep(0.05)
        self.kill_cmd.put(1)

## caput XF:06BMA-OP{Mir:M3-Ax:XU}Mtr_KILL_CMD.PROC 1

## monochromator
dcm_bragg = FMBOEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Bragg}Mtr',  name='dcm_bragg')
dcm_pitch = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:P2}Mtr',   name='dcm_pitch')
dcm_roll  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:R2}Mtr',   name='dcm_roll')
dcm_perp  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Per2}Mtr', name='dcm_perp')
dcm_para  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Par2}Mtr', name='dcm_para')
dcm_x     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:X}Mtr',      name='dcm_x')
dcm_y     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Y}Mtr',      name='dcm_y')


dcm_para.hlm.value = 161        # this is 21200 on the Si(111) mono
#                               # hard limit is at 162.48

dcm_bragg.encoder.kind = 'hinted'
dcm_bragg.user_readback.kind = 'hinted'
dcm_bragg.user_setpoint.kind = 'normal'
dcm_bragg.acceleration.put(BMMuser.acc_fast)

## for some reason, this needs to be set explicitly
dcm_x.hlm.value = 68
dcm_x.llm.value = 0

## collimating mirror
m1_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YU}Mtr',   name='m1_yu')
m1_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YDO}Mtr',  name='m1_ydo')
m1_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M1-Ax:YDI}Mtr',  name='m1_ydi')
m1_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M1-Ax:XU}Mtr',   name='m1_xu')
m1_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M1-Ax:XD}Mtr',   name='m1_yxd')

## focusing mirror
m2_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YU}Mtr',   name='m2_yu')
m2_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDO}Mtr',  name='m2_ydo')
m2_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDI}Mtr',  name='m2_ydi')
m2_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XU}Mtr',   name='m2_xu')
m2_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XD}Mtr',   name='m2_yxd')
m2_bender = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:Bend}Mtr', name='m2_bender')

## front end slits
fe_slits_horizontal1 = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Hrz}Mtr', name='fe_slits_horizontal1')
fe_slits_incline1    = EpicsMotor('FE:C06B-OP{Slt:1-Ax:Inc}Mtr', name='fe_slits_incline1')
fe_slits_o           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:O}Mtr',   name='fe_slits_o')
fe_slits_t           = EpicsMotor('FE:C06B-OP{Slt:1-Ax:T}Mtr',   name='fe_slits_t')
fe_slits_horizontal2 = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Hrz}Mtr', name='fe_slits_horizontal2')
fe_slits_incline2    = EpicsMotor('FE:C06B-OP{Slt:2-Ax:Inc}Mtr', name='fe_slits_incline2')
fe_slits_i           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:I}Mtr',   name='fe_slits_i')
fe_slits_b           = EpicsMotor('FE:C06B-OP{Slt:2-Ax:B}Mtr',   name='fe_slits_b')
fe_slits_hsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}size', name='fe_slits_hsize')
fe_slits_vsize       = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}size', name='fe_slits_vsize')
fe_slits_hcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:X}center', name='fe_slits_hcenter')
fe_slits_vcenter     = EpicsSignalRO('FE:C06B-OP{Slt:12-Ax:Y}center', name='fe_slits_vcenter')

## DM1
dm1_filters1 = XAFSEpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y1}Mtr', name='dm1_filters1')
dm1_filters2 = XAFSEpicsMotor('XF:06BMA-BI{Fltr:01-Ax:Y2}Mtr', name='dm1_filters2')

## DM2
dm2_slits_o = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:O}Mtr', name='dm2_slits_o')
dm2_slits_i = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:I}Mtr', name='dm2_slits_i')
dm2_slits_t = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:T}Mtr', name='dm2_slits_o')
dm2_slits_b = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:B}Mtr', name='dm2_slits_b')
dm2_fs      = XAFSEpicsMotor('XF:06BMA-BI{Diag:02-Ax:Y}Mtr', name='dm2_fs')

## DM3
dm3_fs      = XAFSEpicsMotor('XF:06BM-BI{FS:03-Ax:Y}Mtr',     name='dm3_fs')
dm3_foils   = VacuumEpicsMotor('XF:06BM-BI{Fltr:01-Ax:Y}Mtr', name='dm3_foils')
dm3_bct     = VacuumEpicsMotor('XF:06BM-BI{BCT-Ax:Y}Mtr',     name='dm3_bct')
dm3_bpm     = XAFSEpicsMotor('XF:06BM-BI{BPM:1-Ax:Y}Mtr',     name='dm3_bpm')
dm3_slits_o = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:O}Mtr',    name='dm3_slits_o')
dm3_slits_i = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:I}Mtr',    name='dm3_slits_i')
dm3_slits_t = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:T}Mtr',    name='dm3_slits_t')
dm3_slits_b = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:B}Mtr',    name='dm3_slits_b')

dm3_fs.llm.value = -65

## XAFS table
xafs_yu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YU}Mtr',  name='xafs_yu')
xafs_ydo = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDO}Mtr', name='xafs_ydo')
xafs_ydi = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDI}Mtr', name='xafs_ydi')
xafs_xu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XU}Mtr',  name='xafs_xu')
xafs_xd  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XD}Mtr',  name='xafs_xd')



## XAFS stages
xafs_rotb  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_rotb')
xafs_roth  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotH}Mtr',  name='xafs_roth')
xafs_rots  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotS}Mtr',  name='xafs_rots')
xafs_lins  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinS}Mtr',  name='xafs_lins')
xafs_ref   = xafs_linxs = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinXS}Mtr', name='xafs_linxs')
xafs_x     = xafs_linx  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinX}Mtr',  name='xafs_linx')
xafs_y     = xafs_liny  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:LinY}Mtr',  name='xafs_liny')
xafs_roll  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Pitch}Mtr', name='xafs_roll') # note: the way this stage gets mounted, the
xafs_pitch = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Roll}Mtr',  name='xafs_pitch') # EPICS names are swapped.  sigh....

xafs_wheel  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_wheel.user_offset.put(-31.532)

xafs_ref.llm.value = -95
xafs_ref.hlm.value = 95
xafs_ref.user_offset.put(102)

# RE(scan(dets, m3.pitch, -4, -3, num=10))


def setup_wheel():
    yield from mv(xafs_x, -115.032, xafs_y, 117.94, xafs_wheel, 0)
    
