
#  RE(count([quadem1], 2), DerivedPlot(it_norm, xlabel='energy', ylabel='ratio'))

### ===============================================================================
### plotting axes against I0 (need: individual blade scans for slits3)

def dcmpitch(doc):
    y = doc['data']['I0']
    x = doc['data']['dcm_pitch']
    return x, y

def bctscan(doc):
    x  = doc['data']['dm3_bct']
    y  = doc['data']['I0']
    return x, y

def tablescan(doc):
    x  = doc['data']['xafs_table_vertical']
    y  = doc['data']['I0']
    return x, y

#Plot_pitch_i0 = "DerivedPlot(dcmpitch, xlabel='2nd crystal pitch', ylabel='I0')"
#Plot_slits_i0 = "DerivedPlot(bctscan,  xlabel='slit height',       ylabel='I0')"
### ===============================================================================




### ===============================================================================
### xafs plots

def trans_xmu(doc):
    i0 = doc['data']['I0']
    it = doc['data']['It']
    x  = doc['data']['dcm_energy']
    #x  = doc['seq_num']
    y  = log(i0 / it)
    return x, y

def ref_xmu(doc):
    it = doc['data']['It']
    ir = doc['data']['Ir']
    x  = doc['data']['dcm_energy']
    y  = log(it / ir)
    return x, y

def roi_norm(doc):
    i0   = doc['data']['I0']
    roi1 = doc['data']['ROI1']
    roi2 = doc['data']['ROI2']
    roi3 = doc['data']['ROI3']
    roi4 = doc['data']['ROI4']
    x    = doc['data']['dcm_energy']
    y    = (roi1 + roi2 + roi3 + roi4) / i0
    return x, y

def dt_norm(doc):
    i0   = doc['data']['I0']
    dt1  = doc['data']['DTC1']
    dt2  = doc['data']['DTC2']
    dt3  = doc['data']['DTC3']
    dt4  = doc['data']['DTC4']
    x    = doc['data']['dcm_energy']
    y    = (dt1 + dt2 + dt3 + dt4) / i0
    return x, y

#Plot_e_trans = "DerivedPlot(trans_xmu, xlabel='energy (eV)', ylabel='absorption')"
#Plot_e_fluo  = "DerivedPlot(dt_norm,   xlabel='energy (eV)', ylabel='absorption')"
### ===============================================================================



### ===============================================================================
### motor scans on the xafs table (also need roth, rotb, rots, lins, linxs)

def xscan(doc):
    i0 = doc['data']['I0']
    it = doc['data']['It']
    x  = doc['data']['xafs_linx']
    y  = it / i0
    return x, y

def dt_x(doc):
    i0   = doc['data']['I0']
    dt1  = doc['data']['DTC1']
    dt2  = doc['data']['DTC2']
    dt3  = doc['data']['DTC3']
    dt4  = doc['data']['DTC4']
    x    = doc['data']['xafs_linx']
    y    = (dt1 + dt2 + dt3 + dt4) / i0
    return x, y

def yscan(doc):
    i0 = doc['data']['I0']
    it = doc['data']['It']
    x  = doc['data']['xafs_liny']
    y  = it / i0
    return x, y

def dt_y(doc):
    i0   = doc['data']['I0']
    dt1  = doc['data']['DTC1']
    dt2  = doc['data']['DTC2']
    dt3  = doc['data']['DTC3']
    dt4  = doc['data']['DTC4']
    x    = doc['data']['xafs_liny']
    y    = (dt1 + dt2 + dt3 + dt4) / i0
    return x, y

def rollscan_trans(doc):
    i0 = doc['data']['I0']
    it = doc['data']['It']
    x  = doc['data']['xafs_roll']
    y  = it / i0
    return x, y
def rollscan_fluo(doc):
    i0  = doc['data']['I0']
    dt1 = doc['data']['DTC1']
    dt2 = doc['data']['DTC2']
    dt3 = doc['data']['DTC3']
    dt4 = doc['data']['DTC4']
    x   = doc['data']['xafs_roll']
    y   = (dt1 + dt2 + dt3 + dt4) / i0
    return x, y

def pitchscan_trans(doc):
    i0 = doc['data']['I0']
    it = doc['data']['It']
    x  = doc['data']['xafs_pitch']
    y  = it / i0
    return x, y
def pitchscan_fluo(doc):
    i0  = doc['data']['I0']
    dt1 = doc['data']['DTC1']
    dt2 = doc['data']['DTC2']
    dt3 = doc['data']['DTC3']
    dt4 = doc['data']['DTC4']
    x   = doc['data']['xafs_pitch']
    y   = (dt1 + dt2 + dt3 + dt4) / i0
    return x, y

#Plot_x_it = "DerivedPlot(xscan, xlabel='X', ylabel='it/i0')"
#Plot_x_if = "DerivedPlot(dt_x,  xlabel='X', ylabel='if/i0')"
#Plot_y_it = "DerivedPlot(yscan, xlabel='Y', ylabel='it/i0')"
#Plot_y_if = "DerivedPlot(dt_y,  xlabel='Y', ylabel='if/i0')"
### ===============================================================================
