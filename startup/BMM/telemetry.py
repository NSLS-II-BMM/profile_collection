from databroker import catalog
from databroker.queries import TimeRange
import numpy, json, os, time
from tqdm import tqdm           # progress bar

from BMM.periodictable import element_symbol, edge_energy, Z_number

from bluesky_queueserver.manager.profile_tools import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns


class BMMTelementry():
    '''A class for figuring out the historical average overhead for an
    XAS scan at BMM

    "Overhead" is defined as the excess time beyond the measurement
    time.  The time span of the scan is computed from the time stamps
    in the start and stop document.  The measurement time is the sum
    of the dwell time column in the datatable from the measurement.

    '''
    def __init__(self):
        self.folder      = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup', 'telemetry')
        self.json        = os.path.join(self.folder, 'telemetry.json')
        self.bc          = catalog['bmm']
        self.start_date  = '2019-09-01'
        self.reliability = 10
        self.beamdump    = 3
        ###                         k-edges               l-edges
        self.all_elements = list(range(22, 46)) + list(range(55, 93))

        
    def records(self, element=None):
        query          = TimeRange(since=self.start_date, until='2040')
        time_search    = self.bc.search(query)
        xafs_search    = time_search.search({'XDI._kind':'xafs'})
        element_search = xafs_search.search({'XDI.Element.symbol': element})
        print(f'Number of records for {element} since {self.start_date}: {len(element_search)}')
        return(element_search)

    @set_user_ns
    def overhead(self, element=None):
        if element is None: return(0)
        db = user_ns['db']
        element_search = self.records(element)
        ratio, difference, dpp = numpy.array([]), numpy.array([]), numpy.array([])
        l = len(list(element_search))
        if l == 0: return(0)
        count = 0
        for u in tqdm(list(element_search)):
            
            this=db.v2[u]

            ## records that did not complete normally
            if 'primary' in this.metadata['stop']['num_events']:
                if this.metadata['start']['num_points'] != this.metadata['stop']['num_events']['primary']:
                    continue
            try:
                t = this.primary.read()['dwti_dwell_time']
                measurement_time = float(t.sum())
                elapsed_time = this.metadata['stop']['time'] - this.metadata['start']['time']

                ## records that scan beam dumps or other pauses would skew the statistics
                if elapsed_time/measurement_time > self.beamdump:
                    continue

                difference = numpy.append(difference, (elapsed_time - measurement_time))
                ratio = numpy.append(ratio, elapsed_time/measurement_time)
                diff_per_point = (elapsed_time - measurement_time) / len(t)
                dpp = numpy.append(dpp, diff_per_point)
                count = count + 1
            except:
                pass
        return({'count'     : count,
                'ratio'     : [ratio.mean(), ratio.std()],
                'difference': [difference.mean(), difference.std()],
                'dpp'       : [dpp.mean(), dpp.std()],
            })
    

    ## TODO: take a list of integers/element symbols as an input
    ## parameter, extract just those, modify json file for those
    ## elements
    def periodic_table(self, el=None):
        start = time.time()
        results = {}
        for z in self.all_elements:
            el = element_symbol(z)
            results[el] = self.overhead(el)
            
        j = json.dumps(results)
        f = open(self.json,"w")
        f.write(j)
        f.close()
        end = time.time()
        print('\n\nThat took %.1f min' % ((end-start)/60))
        

    def interpolate(self, energy):
        a = json.load(open(self.json))
        e, t = numpy.array([]), numpy.array([])
        for z in self.all_elements:
            if 'count' not in a[element_symbol(z)]:
                continue
            if a[element_symbol(z)]['count'] < self.reliability:
                continue
            t = numpy.append(t, a[element_symbol(z)]['dpp'][0])
            if z < 46:
                e=numpy.append(e, edge_energy(z, 'k'))
            else:
                e=numpy.append(e, edge_energy(z, 'l3'))
                             
        s=numpy.argsort(e)
        return(numpy.interp(energy, e[s], t[s]))

    def overhead_per_point(self, element, edge=None):
        a = json.load(open(self.json))
        element = element_symbol(element)
        if edge is not None and edge.lower() in ('l2', 'l1'):
            return([self.interpolate(edge_energy(element, edge)), 0])
        if element in a and 'dpp' in a[element]:
            return(a[element]['dpp'])
        else:
            if edge is None or edge.lower() not in ('l2', 'l1'):
                edge = 'k'
                if Z_number(element) > 45:
                    edge = 'l3'
            return([self.interpolate(edge_energy(element, edge)), 0])
        
