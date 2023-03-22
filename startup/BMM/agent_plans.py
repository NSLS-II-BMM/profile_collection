from typing import Sequence

import bluesky.preprocessors as bpp
import msgpack
import redis
from bluesky import plan_stubs as bps
from BMM.edge import change_edge
from BMM.user_ns.instruments import slits3
from BMM.user_ns.motors import xafs_det
from BMM.xafs import xafs
from confluent_kafka import Producer
from nslsii import _read_bluesky_kafka_config_file

__all__ = ["agent_driven_nap", "agent_move_and_measure"]


@bpp.run_decorator()
def agent_driven_nap(delay: float, *, delay_kwarg: float = 0, md=None):
    """Ensuring we can auto add 'agent_' plans and use args/kwargs"""
    if delay_kwarg:
        yield from bps.sleep(delay_kwarg)
    else:
        yield from bps.sleep(delay)


def agent_directive(tla, name, doc):
    """
    Issue any directive to a listening agent by name/uid.

    Parameters
    ----------
    tla : str
        Beamline three letter acronym
    name : str
        Unique agent name. These are generated using xkcdpass for names like:
        "agent-exotic-farm"
        "xca-clever-table"
    doc : dict
        This is the message to pass to the agent. It must take the form:
        {"action": method_name,
         "args": (arguments,),
         "kwargs: {keyword:argument}
        }

    Returns
    -------

    """
    kafka_config = _read_bluesky_kafka_config_file("/etc/bluesky/kafka.yml")
    producer_config = dict()
    producer_config.update(kafka_config["runengine_producer_config"])
    producer_config["bootstrap.servers"] = ",".join(kafka_config["bootstrap_servers"])
    agent_producer = Producer(producer_config)

    # All 3 steps should happen for each message publication
    agent_producer.produce(topic=f"{tla}.mmm.bluesky.agents", key="", value=msgpack.dumps((name, doc)))
    agent_producer.poll(0)
    agent_producer.flush()
    yield from bps.null()


def agent_measure_single_edge(motor_x, x_position, motor_y, y_position, *, md=None, **kwargs):
    """
    A complete XAFS measurement for a single edge.
    The element edge must have its own calibrated motor positioning and detector distance.
    The sample is moved into position, and spectra taken. The edge is assumed to be set.

    Parameters
    ----------
    motor_x : str
        Positional motor for sample in x.
    x_position : float
        Absolute x motor position for sample measurement (This is the real independent variable)
    motor_y : str
        Positional motor for sample in y.
    y_position : float
        Absolute y motor position for sample measurement
    md : Optional[dict]
        Metadata
    kwargs :
        All keyword arguments for the xafs plan. Must include  'filename'. Eg below:
            >>> {'filename': 'Cu_PdCuCr_112421_001',
            >>> 'nscans': 1,
            >>> 'start': 'next',
            >>> 'mode': 'fluorescence',
            >>> 'element': 'Cu',
            >>> 'edge': 'K',
            >>> 'sample': 'PdCuCr',
            >>> 'preparation': 'film deposited on something',
            >>> 'comment': 'index = 1, position (x,y) = (-9.04, -31.64), center at (236.98807533, 80.98291381)',
            >>> 'bounds': '-200 -30 -10 25 12k',
            >>> 'steps': '10 2 0.3 0.05k',
            >>> 'times': '0.5 0.5 0.5 0.5'}
    """
    rkvs = redis.Redis(host="xf06bm-ioc2", port=6379, db=0)
    element = rkvs.get("BMM:pds:element").decode("utf-8")
    edge = rkvs.get("BMM:pds:edge").decode("utf-8")
    yield from bps.mv(motor_x, x_position)
    _md = dict(x_position=motor_x.position, redis_element=element, redis_edge=edge)
    yield from bps.mv(motor_y, y_position)
    _md["det_position"] = xafs_det.position
    _md.update(md or {})
    yield from xafs(comment=str(_md), **kwargs)


def agent_move_and_measure(
    motor_x,
    elem1_x_position,
    elem2_x_position,
    motor_y,
    elem1_y_position,
    elem2_y_position,
    elem1_det_position,
    elem2_det_position,
    *,
    elements: Sequence[str],
    edges: Sequence[str],
    md=None,
    **kwargs,
):
    """
    A complete XAFS measurement for the Cu/Ti sample.
    Each element edge must have it's own calibrated motor positioning and detector distance.
    The sample is moved into position, edge changed and spectra taken.
    Parameters
    ----------
    motor_x :
        Positional motor for sample in x.
    elem1_x_position : float
        Absolute motor position for Cu measurement (This is the real independent variable)
    elem2_x_position : float
        Absolute motor position for Ti measurement
    motor_y :
        Positional motor for sample in y.
    elem1_y_position : float
        Absolute motor position for Cu measurement
    elem2_y_position : float
        Absolute motor position for Ti measurement
    elem1_det_position : float
        Absolute motor position for the xafs detector for the Cu measurement.
    elem2_det_position : float
        Absolute motor position for the xafs detector for the Ti measurement.
    elements : Sequence[str]
        List of element symbols
    edges: Sequence[str]
        List of edges corresponding to elements

    md : Optional[dict]
        Metadata
    kwargs :
        All keyword arguments for the xafs plan. Must include  'filename'. Eg below:
            >>> {'filename': 'Cu_PdCuCr_112421_001',
            >>> 'nscans': 1,
            >>> 'start': 'next',
            >>> 'mode': 'fluorescence',
            >>> 'element': 'Cu',
            >>> 'edge': 'K',
            >>> 'sample': 'PdCuCr',
            >>> 'preparation': 'film deposited on something',
            >>> 'comment': 'index = 1, position (x,y) = (-9.04, -31.64), center at (236.98807533, 80.98291381)',
            >>> 'bounds': '-200 -30 -10 25 12k',
            >>> 'steps': '10 2 0.3 0.05k',
            >>> 'times': '0.5 0.5 0.5 0.5'}
    """

    def elem1_plan():
        yield from bps.mv(motor_x, elem1_x_position)
        _md = {f"{elements[0]}_position": motor_x.position}
        yield from bps.mv(motor_y, elem1_y_position)
        yield from bps.mv(xafs_det, elem1_det_position)
        _md[f"{elements[0]}_det_position"] = xafs_det.position
        _md.update(md or {})
        yield from bps.mv(slits3.vsize, 0.1)
        if rkvs.get("BMM:pds:element").decode("utf-8") != elements[0]:
            yield from change_edge(elements[0], focus=True)
        # xafs doesn't take md, so stuff it into a comment string to be ast.literal_eval()
        yield from xafs(element=elements[0], edge=edges[0], comment=str(_md), **kwargs)

    def elem2_plan():
        yield from bps.mv(motor_x, elem2_x_position)
        _md = {f"{elements[1]}_position": motor_x.position}
        yield from bps.mv(motor_y, elem2_y_position)
        yield from bps.mv(xafs_det, elem2_det_position)
        _md[f"{elements[1]}_det_position"] = xafs_det.position
        _md.update(md or {})
        yield from bps.mv(slits3.vsize, 0.3)
        if rkvs.get("BMM:pds:element").decode("utf-8") != elements[1]:
            yield from change_edge(elements[1], focus=True)
        yield from xafs(element=elements[1], edge=edges[1], comment=str(_md), **kwargs)

    rkvs = redis.Redis(host="xf06bm-ioc2", port=6379, db=0)
    element = rkvs.get("BMM:pds:element").decode("utf-8")
    # edge = rkvs.get('BMM:pds:edge').decode('utf-8')
    if element == elements[1]:
        yield from elem2_plan()
        yield from elem1_plan()
    else:
        yield from elem1_plan()
        yield from elem2_plan()


def agent_move_motor(motor_x, Cu_x_position, *args, **kwargs):
    yield from bps.mv(motor_x, Cu_x_position)


def agent_change_edge(element):
    yield from change_edge(element, focus=True)


def agent_xafs(
    motor_x,
    Cu_x_position,
    Ti_x_position,
    motor_y,
    Cu_y_position,
    Ti_y_position,
    *,
    Cu_det_position,
    Ti_det_position,
    md=None,
    **kwargs,
):
    _md = dict(Cu_position=motor_x.position)
    _md["Cu_det_position"] = xafs_det.position
    _md.update(md or {})
    yield from xafs(element="Cu", **kwargs)
