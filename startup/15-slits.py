
from BMM.slits import Slits, GonioSlits

run_report(__file__, text='coordinated slit motion')


sl = slits3 = Slits('XF:06BM-BI{Slt:02-Ax:',  name='slits3')
slits3.nominal = [7.0, 1.0, 0.0, 0.0]
slits2 = Slits('XF:06BMA-OP{Slt:01-Ax:',  name='slits2')
slits2.nominal = [18.0, 1.1, 0.0, 0.6]
slits2.top.user_offset.put(-0.038)
slits2.bottom.user_offset.put(0.264)

def recover_slits2():
    yield from abs_set(dm2_slits_t.home_signal, 1)
    yield from abs_set(dm2_slits_i.home_signal, 1)
    yield from sleep(1.0)
    print('Begin homing %s motors:\n' % slits2.name)
    hvalues = (dm2_slits_t.hocpl.get(), dm2_slits_b.hocpl.get(), dm2_slits_i.hocpl.get(), dm2_slits_o.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (dm2_slits_t.hocpl.get(), dm2_slits_b.hocpl.get(), dm2_slits_i.hocpl.get(), dm2_slits_o.hocpl.get())
        strings = ['top', 'bottom', 'inboard', 'outboard']
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(slits2.hsize,   slits2.nominal[0])
    yield from mv(slits2.vsize,   slits2.nominal[1])
    yield from mv(slits2.hcenter, slits2.nominal[2])
    yield from mv(slits2.vcenter, slits2.nominal[3])

def recover_slits3():
    yield from abs_set(dm3_slits_t.home_signal, 1)
    yield from abs_set(dm3_slits_i.home_signal, 1)
    yield from sleep(1.0)
    print('Begin homing %s motors:\n' % slits3.name)
    hvalues = (dm3_slits_t.hocpl.get(), dm3_slits_b.hocpl.get(), dm3_slits_i.hocpl.get(), dm3_slits_o.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (dm3_slits_t.hocpl.get(), dm3_slits_b.hocpl.get(), dm3_slits_i.hocpl.get(), dm3_slits_o.hocpl.get())
        strings = ['top', 'bottom', 'inboard', 'outboard']
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(slits3.hsize,   slits3.nominal[0])
    yield from mv(slits3.vsize,   slits3.nominal[1])
    yield from mv(slits3.hcenter, slits3.nominal[2])
    yield from mv(slits3.vcenter, slits3.nominal[3])

        
slitsg = GonioSlits('XF:06BM-ES{SixC-Ax:Slt1_',  name='slitsg')

