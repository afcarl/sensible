from __future__ import division

import pytest
import zmq

from sensible.sensors.sensible_threading import StoppableThread
from sensible.tracking.track_specialist import TrackSpecialist
from sensible.tracking.track_state import TrackState
from sensible.sensors.DSRC import DSRC


class MockSensor(StoppableThread):
    """
    A mock class to emulate a sensor publishing a stream of measurements
    for the track specialist
    """
    def __init__(self, topic_filters, test_msgs, port=6667, name="MockSensor"):
        super(MockSensor, self).__init__(name)
        self._port = port
        self._topic_filters = topic_filters

        context = zmq.Context()
        self._pub = context.socket(zmq.PUB)
        self._pub.bind("tcp://*:{}".format(port))

        # Cycle through these messages
        self._test_msgs = test_msgs
        self._msg_idx = 0

    def run(self):
        while not self.stopped():
            for t_filter in self._topic_filters:

                self._pub.send_string("{} {}".format(t_filter, self._test_msgs[self._msg_idx]))
                self._msg_idx = (1 + self._msg_idx) % len(self._test_msgs)


def fake_msg():
    """Return a fake DSRC message for tests"""
    return {
        'msg_count': 0,
        'id': 123,
        'h': 14,
        'm': 14,
        's': 14,
        'lat': 29.12123,
        'lon': -82.345234,
        'heading': 0,
        'speed': 20,
        'lane': 1,
        'veh_len': 15,
        'max_accel': 3.2,
        'max_decel': -3.2,
        'served': 0
    }


def get_track_specialist(tmpdir, bsm_port=6669, run_for=20.0, frequency=5):
    """Return a standard TrackSpecialist object for testing."""
    sensor_ports = [6667, 6668]
    topic_filters = ["DSRC", "Radar"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}
    p = tmpdir.mkdir("logs").join("test.txt")
    return TrackSpecialist(sensors, bsm_port, run_for, p, frequency=frequency)


def test_initialize_track_specialist(tmpdir):
    """Test that the TrackSpecialist constructor initializes the connection to a sensor
    correctly with the proper topic filters
    """
    track_specialist = get_track_specialist(tmpdir)
    test_message = ['test']

    mock_sensor = MockSensor(["DSRC"], test_message)
    mock_sensor.start()

    # assert that each connection is open
    attempts = 0
    max_attempts = 10000

    DONE = False
    while attempts < max_attempts:
        for (topic, subscriber) in track_specialist.subscribers.items():
            try:
                string = subscriber.recv_string(flags=zmq.NOBLOCK)
                msg_topic, msg = string.split(" ")
                assert msg_topic == topic
                assert msg == test_message[0]
                DONE = True
            except zmq.Again as err:
                continue

        attempts += 1
        if DONE:
            break

    mock_sensor.stop()
    if attempts == max_attempts:
        pytest.fail('Exceeded max attempts to send/recv messages')


def test_track_drop(tmpdir):
    """Test that the main `run` method works as expected
        1. Exits after `run_for` seconds pass.
        2.  Tracks that don't receive new measurements are dropped."""
    track_specialist = get_track_specialist(tmpdir, run_for=3)
    msg = fake_msg()
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.n_consecutive_measurements == 1
    assert track.n_consecutive_missed == 0

    # Run for 3 seconds with no messages incoming
    track_specialist.run()

    assert track.track_state == TrackState.DEAD
    assert msg['id'] not in track_specialist.sensor_id_map
    assert track_id not in track_specialist.track_list


def test_track_creation(tmpdir):
    """This tests whether a new track is created with
    the correct state, i.e., UNCONFIRMED, by
    track_specialist.create_track(msg). """
    track_specialist = get_track_specialist(tmpdir)
    msg = fake_msg()
    track_specialist.create_track(msg, DSRC.topic())
    assert msg['id'] in track_specialist.sensor_id_map
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED
    assert track.n_consecutive_measurements == 1
    assert track.n_consecutive_missed == 0
    assert track.received_measurement


def test_vehicle_id_association(tmpdir):
    """This tests whether new measurements can be matched to
    existing tracks based on ID"""
    track_specialist = get_track_specialist(tmpdir)
    msg = fake_msg()
    # 1st message
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track_specialist.track_list[track_id].received_measurement = False
    # 2nd message
    msg['s'] = 15
    track_specialist.measurement_association("DSRC", msg)
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED
    assert track.n_consecutive_measurements == 2
    assert track.n_consecutive_missed == 0
    assert track.received_measurement


def test_vehicle_id_association_no_match(tmpdir):
    """This tests whether an unconfirmed track is created
    when no vehicle ID match is found"""
    track_specialist = get_track_specialist(tmpdir)
    msg = fake_msg()
    # Try to associate a new msg - should call create_track
    track_specialist.measurement_association("DSRC", msg)
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED
    assert track.n_consecutive_measurements == 1
    assert track.n_consecutive_missed == 0
    assert track.received_measurement


def test_vehicle_bsm_publisher():
    """This tests whether a BSM is generated for each
    CONFIRMED vehicle track that has not yet been served
    a trajectory"""
    pytest.fail('Unimplemented test')


def test_track_state_confirm(tmpdir):
    """This tests that an UNCONFIRMED track becomes
    confirmed after M consecutive messages arrive for that
    track, where M is the threshold."""
    track_specialist = get_track_specialist(tmpdir)
    msg = fake_msg()
    # Try to associate a new msg - should call create_track
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    track.received_measurement = False
    assert track.track_state == TrackState.UNCONFIRMED
    track.n_consecutive_measurements = track_specialist.track_confirmation_threshold
    # One more message than the threshold causes the state to change
    # to CONFIRMED
    track_specialist.measurement_association("DSRC", msg)
    assert track.track_state == TrackState.CONFIRMED


def test_track_state_zombie_to_unconfirmed(tmpdir):
    """This tests that an UNCONFIRMED track
    becomes a ZOMBIE after missing N consecutive messages,
    where N is the zombie threshold."""
    # Assume the frequency is 5 Hz
    # Need to run for 1.2 seconds because after track creation,
    # received_msg is set to 1 for one iteration of the loop
    track_specialist = get_track_specialist(tmpdir, run_for=0.8)
    msg = fake_msg()
    # Try to associate a new msg - should call create_track
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED

    # run for 0.8 seconds
    track_specialist.run()

    assert track_id in track_specialist.track_list
    assert track.track_state == TrackState.ZOMBIE
    assert track.n_consecutive_missed == 3


def test_track_state_confirmed_to_zombie(tmpdir):
    """This tests that a CONFIRMED track
    becomes a ZOMBIE after missing N consecutive messages,
    where N is the zombie threshold."""
    # Assume the frequency is 5 Hz
    # Need to run for 1.2 seconds because after track creation,
    # received_msg is set to 1 for one iteration of the loop
    track_specialist = get_track_specialist(tmpdir, run_for=0.8)
    msg = fake_msg()
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED
    track.step()
    track.fuse_empty()
    track.received_measurement = False

    track.n_consecutive_measurements = track_specialist.track_confirmation_threshold
    track_specialist.measurement_association("DSRC", msg)

    assert track.track_state == TrackState.CONFIRMED

    # run for 0.8 seconds
    track_specialist.run()

    assert track_id in track_specialist.track_list
    assert track.track_state == TrackState.ZOMBIE
    assert track.n_consecutive_missed == 3


def test_track_recovery(tmpdir):
    """This tests whether a track can recover from ZOMBIE
    state to UNCONFIRMED if a new message for it arrives
    before it is deleted"""
    track_specialist = get_track_specialist(tmpdir, run_for=0.8)
    msg = fake_msg()
    track_specialist.create_track(msg, DSRC.topic())
    track_id = track_specialist.sensor_id_map[msg['id']]
    track = track_specialist.track_list[track_id]
    assert track.track_state == TrackState.UNCONFIRMED
    track_specialist.run()

    assert track.track_state == TrackState.ZOMBIE

    track_specialist.measurement_association("DSRC", msg)

    assert track.track_state == TrackState.UNCONFIRMED
    assert track.n_consecutive_measurements == 1
    assert track.n_consecutive_missed == 0
