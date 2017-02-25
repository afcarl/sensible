from __future__ import absolute_import

import xml.etree.cElementTree as ElementTree
import sensible.util.ops as ops
import pytest

from sensible.sensors.DSRC import DSRC
from sensible.util.exceptions import ParseError


def test_xml_parsing():
    """Test parsing a CSM from XML"""

    with open("data/csm-nb.txt") as f:
        csm = f.read()
        root = ElementTree.fromstring(csm)
        assert root.tag == "ConnectedSafetyMessage"
        data = root.find('blob1').text
        data = ''.join(data.split())
        assert len(data) == 58


def test_csm_parsing0():
    """Test that a csm can be parsed correctly."""
    dsrc = DSRC("", 4200)

    with open("data/csm-nb.txt") as f:
        csm = f.read()
        result = dsrc.parse(csm)

        assert result['msg_count'] == 126
        assert result['veh_id'] == '2E7C0E21'
        assert result['lane'] == 8
        assert result['max_accel'] == 3.0
        assert result['max_decel'] == -3.0
        assert result['h'] == 0
        assert result['m'] == 0
        assert result['s'] == 0
        assert result['speed'] == 8
        assert result['lat'] == 29.644256
        assert result['lon'] == -82.346891
        assert result['heading'] == 0.0
        assert result['served'] == 0


def test_csm_parsing1():
    """Test that a bad message is ignored and a ParseError is thrown"""
    dsrc = DSRC("", 4200)

    with open("data/csm-nb-bad.txt") as f:
        csm = f.read()
        with pytest.raises(ParseError):
            _ = dsrc.parse(csm)


def test_lat_lon():
    """Test decoding latitude and longitude"""

    with open("data/csm-nb.txt") as f:
        csm = f.read()
        root = ElementTree.fromstring(csm)
        data = root.find('blob1').text
        data = ''.join(data.split())

        lat = ops.twos_comp(int(data[18:26], 16), 32) * 1e-7
        lon = ops.twos_comp(int(data[26:34], 16), 32) * 1e-7

        assert lat == 29.644256
        assert lon == -82.346891


def test_push_msg0():
    """Test that a non-unique message won't get added"""
    dsrc = DSRC("", 4200)

    test0 = {
        'msg_count': 0,
        'veh_id': 123,
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
        'veh_id': 123,
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

    dsrc.queue.append(test0)
    assert len(dsrc.queue) == 1
    dsrc.push(test1)
    assert len(dsrc.queue) == 1
    test1['s'] = 34000.00
    dsrc.push(test1)
    assert len(dsrc.queue) == 2
