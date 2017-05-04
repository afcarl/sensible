from __future__ import absolute_import
from __future__ import division

import xml.etree.cElementTree as ElementTree
import pytest
import zmq
import time

import sensible.util.ops as ops

from sensible.sensors.DSRC import DSRC
from sensible.sensors.synchronizer import Synchronizer
from sensible.sensors.sensible_threading import SocketThread
from sensible.tracking.vehicle_type import VehicleType

from .sensor_emulator import SensorEmulator

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle

# def test_csm_parsing0():
#     """Test that a csm can be parsed correctly."""
#     dsrc = DSRC("", remote_port=4200, local_port=6666)
#
#     with open("data/csm-nb.txt") as f:
#         csm = f.read()
#         result = dsrc.parse(csm)
#
#         assert result['msg_count'] == 126
#         assert result['id'] == 779882017
#         assert result['lane'] == 8
#         assert result['max_accel'] == 3.0
#         assert result['max_decel'] == -3.0
#         assert result['h'] == 0
#         assert result['m'] == 0
#         assert result['s'] == 0
#         assert result['speed'] == 8
#         assert result['lat'] == 29.644256
#         assert result['lon'] == -82.346891
#         assert result['heading'] == 0.0
#         assert result['served'] == 0
#
#         assert DSRC.get_default_vehicle_type(id=result['id']) == VehicleType.AUTOMATED


def test_csm_parsing2():

    with open("data/test_csm.txt") as f:
        csm = f.read()
        result = DSRC.parse(csm)
        assert result['served'] == 0


# def test_lat_lon():
#     """Test decoding latitude and longitude"""
#
#     with open("data/csm-nb.txt") as f:
#         csm = f.read()
#         root = ElementTree.fromstring(csm)
#         data = root.find('blob1').text
#         data = ''.join(data.split())
#
#         lat = ops.twos_comp(int(data[18:26], 16), 32) * 1e-7
#         lon = ops.twos_comp(int(data[26:34], 16), 32) * 1e-7
#
#         assert lat == 29.644256
#         assert lon == -82.346891


def test_push_msg0():
    """Test pushing new messages onto the queue."""
    dsrc = DSRC()
    synchronizer = Synchronizer(publish_freq=5, queue=dsrc.queue,
                                port=4200, topic=dsrc.topic(), name="DSRCSynchronizer")

    test0 = {
        'msg_count': 0,
        'id': 123,
        'h': 8,
        'm': 16,
        's': 32000.00,
        'lat': 29.12,
        'lon': -87.234,
        'heading': 0,
        'speed': 0,
        'lane': 0,
        'veh_len': 15,
        'max_accel': 10,
        'max_decel': -17,
        'served': 0
    }

    test1 = {
        'msg_count': 0,
        'id': 123,
        'h': 8,
        'm': 16,
        's': 32000.00,
        'lat': 29.12,
        'lon': -87.234,
        'heading': 0,
        'speed': 0,
        'lane': 0,
        'veh_len': 15,
        'max_accel': 10,
        'max_decel': -17,
        'served': 0
    }

    dsrc.add_to_queue(test0)
    assert len(synchronizer.queue) == 1
    dsrc.add_to_queue(test1)
    # don't add message with same id and seconds
    assert len(synchronizer.queue) == 1
    test1['s'] = 34000.00
    dsrc.add_to_queue(test1)
    assert len(synchronizer.queue) == 2


def test_synchronization():
    """Test the Pub/Sub component of the DSRC thread"""
    remote_port = 4200
    local_port = 6666

    sensor = DSRC()
    dsrc = SocketThread(sensor=sensor, ip_address="localhost", port=remote_port, msg_len=300, name="DSRCThread")

    synchronizer = Synchronizer(publish_freq=5, queue=sensor.queue,
                                port=local_port, topic=DSRC.topic(), name="DSRCSynchronizer", verbose=True)
    # Subscriber
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:{}".format(local_port))
    t_filter = "DSRC"
    if isinstance(t_filter, bytes):
        t_filter = t_filter.decode('ascii')
    subscriber.setsockopt_string(zmq.SUBSCRIBE, t_filter)

    radio = SensorEmulator(port=remote_port, pub_freq=21, file_names=["data/test_csm.txt"])

    # Connect and start the DSRC thread.
    try:
        synchronizer.start()
        # start the DSRC thread
        dsrc.start()
    except Exception:
        pytest.fail("Unable to connect DSRC thread.")

    # Process for 2.2 seconds, 1 message will be dropped due to start-up time
    t_end = time.time() + 2.2
    msgs = []
    radio.start()
    while time.time() < t_end:
        try:
            string = subscriber.recv_string(flags=zmq.NOBLOCK)
            topic, msg = string.split(" ")
            msgs.append(pickle.loads(str(msg)))
        except zmq.Again as e:
            continue

    # Stop the DSRC sender and receiver
    dsrc.stop()
    synchronizer.stop()
    radio.stop()

    # Expect to only receive 10 messages
    assert len(msgs) == 10
















