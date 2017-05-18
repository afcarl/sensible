from sensible.sensors.radar import Radar
from sensible.util import ops


def single_hypothesis_track_association(track_list, query_track_info, threshold, method="track-to-track", verbose=False):
    """
    Single-hypothesis association

    Using Chi-squared tables for 4 degrees of freedom (one for each
    dimension of the state vector), for different p-values

    p = 0.05 -> 9.49
    p = 0.01 -> 13.28
    p = 0.001 -> 18.47

    For 2 DOF

    p = 0.05 -> 5.99
    p = 0.01 -> 9.21

    Result codes
    ============
    0x1 : query is a radar track and association w/ DSRC failed; change type to CONVENTIONAL.
          Associated track id is the query track id.
    0x2 : query is a radar track and association w/ DSRC succeeded; **Can eliminate old radar track and dsrc track.**
          Create a new CONFIRMED fused track.
    0x3 : query is a DSRC track and association w/ radar failed; send BSM if not yet served
          Associated track id is the query track id.
    0x4 : query is a DSRC track and association w/ radar succeeded; change type of the radar track to CONNECTED/AUTOMATED
          and update radar track id to match that of query_track. **Can drop radar track.**
    0x5:  query is a radar measurement from a zone detection and association with a DSRC track failed. Send BSM for a
          new conventional vehicle.
    0x6:  query is a radar measurement from a zone detection and association with a DSRC track succeeded. Change track
          state to fused. Send BSM if not yet served.

    :param track_list: List of (id, track) pairs
    :param threshold: chi-squared threshold
    :param query_track_info: Tuple of (id, track) for track-to-track, otherwise it is the measurement that is to be associated
    :param method: options are "track-to-track" and "measurement-to-track"
    :param verbose: display verbose information
    :return: tuple (result code, associated track id)
    """
    ###########
    # For Debug
    ###########
    # t = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
    #
    # gnn_dict = {'time': t.to_fname_string(), 'radar': radar_measurement}
    # ops.dump(gnn_dict,
    #      "C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\data\\trajectories\\radar-" + t.to_fname_string() + ".pkl")

    results = []

    for (track_id, track) in track_list.items():

        if method == "track-to-track":
            query_track_id = query_track_info[0]
            query_track = query_track_info[1]
            # First condition ensures the query track isn't fused with itself,
            # and the second condition ensures two radar or two DSRC tracks
            # aren't fused together
            if track == query_track or track.sensor == query_track.sensor or track_id in query_track.fused_track_ids:
                continue

            # track-to-track association between tracks
            md, ts1, ts2 = track.state_estimator.TTTA(query_track)
        elif method == "measurement-to-track":

            md, ts1, ts2 = track.state_estimator.TTMA(query_track_info)

        ops.show("  [TTMA] Track {} has a mahalanobis distance of {} "
                 "to the query with time-alignment of {} and {} respectively\n".format(track_id, md, ts1, ts2),
                 verbose)

        if md <= threshold:
            results.append((track_id, md))

    # radar_t_stamp = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
    # radar_log_str = " [GNN] Radar msg: {},{},{},{},{}\n".format(
    #     radar_t_stamp.to_string(), radar_measurement[0], radar_measurement[2],
    #     radar_measurement[1], radar_measurement[3]
    # )
    # print(radar_log_str)

    if method == "track-to-track":
        sensor = query_track.sensor.topic()
    elif method == "measurement-to-track":
        sensor = Radar.topic()

    # Association "failed"
    if len(results) == 0:
        # measurement didn't fall near any tracked vehicles, so if a radar track tentatively
        # associate as a conventional vehicle
        if sensor == Radar.topic():
            if method == "track-to-track":
                ops.show("  [TTTA] New conventional vehicle detected\n", verbose)
                return 0x1, None
            elif method == "measurement-to-track":
                ops.show("  [TTMA] No matching DSRC track for radar detection, classifying as conventional\n", verbose)
                return 0x5, None
        else:
            ops.show("  [TTTA] No matching radar track for DSRC track {}\n".format(query_track_id), verbose)
            return 0x3, None
    else:
        if len(results) > 1:
            ops.show("  [Warning] {} vehicles within gating region of radar detection!\n".format(len(results)), verbose)
            # choose the closest
            #sorted_results = sorted(results, key=lambda pair: len(pair[1]))
            #res_id = sorted_results[0][0]
            res_id = results[0]
            ops.show("  [TTTA] Associating with closest track {}\n".format(res_id), verbose)
            if sensor == Radar.topic():
                if method == "track-to-track":
                    return 0x2, res_id
                elif method == "measurement-to-track":
                    return 0x6, res_id
            else:
                return 0x4, res_id
        else:
            r = results[0]
            if sensor == Radar.topic():
                if method == "track-to-track":
                    ops.show("  [TTTA] Associating radar track {} with DSRC track {}\n".format(query_track_id, r[0]), verbose)
                    return 0x2, r[0]
                elif method == "measurement-to-track":
                    ops.show("  [TTMA] Associating radar detection with track {}\n".format(r[0]), verbose)
                    return 0x6, r[0]
            else:
                ops.show("  [TTTA] Associating DSRC track {} with radar track {}\n".format(query_track_id, r[0]), verbose)
                return 0x4, r[0]
