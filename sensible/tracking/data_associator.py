from sensible.util import ops
from sensible.sensors.radar import Radar
from sensible.sensors.DSRC import DSRC
from sensible.tracking import radar_track_cfg


def single_hypothesis_track_association(track_list, query, method="track-to-track", verbose=False):
    """
    Single-hypothesis track-to-track association

    Using Chi-squared tables for 4 degrees of freedom (one for each
    dimension of the state vector), for different p-values

    p = 0.05 -> 9.49
    p = 0.01 -> 13.28
    p = 0.001 -> 18.47

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
    :param query: The track or measurement that is to be associated
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
            # First condition ensures the query track isn't fused with itself,
            # and the second condition ensures two radar or two DSRC tracks
            # aren't fused together
            if track_id == query.id or track.sensor == query.sensor:
                continue

            md = track.state_estimator.mahalanobis(query.state_estimator.state(),
                                                   query.state_estimator.process_covariance())
        elif method == "measurement-to-track":

            md = track.state_estimator.mahalanobis(query, radar_track_cfg.RadarTrackCfg(0.1).R)

        ops.show("  [Track association] Track {} has a mahalanobis distance of {} "
                 "to the detection".format(track_id, md), verbose)

        if md <= 9.488:
            results.append((track_id, md))

    # radar_t_stamp = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
    # radar_log_str = " [GNN] Radar msg: {},{},{},{},{}\n".format(
    #     radar_t_stamp.to_string(), radar_measurement[0], radar_measurement[2],
    #     radar_measurement[1], radar_measurement[3]
    # )
    # print(radar_log_str)

    if method == "track-to-track":
        sensor = query.sensor
    elif method == "measurement-to-track":
        sensor = Radar

    # Association "failed"
    if len(results) == 0:
        # measurement didn't fall near any tracked vehicles, so if a radar track tentatively
        # associate as a conventional vehicle
        if sensor == Radar:
            if method == "track-to-track":
                ops.show("  [Track association] Conventional vehicle detected", verbose)
                return 0x1, query.id
            elif method == "measurement-to-track":
                ops.show("  [Measurement association] No matching DSRC track, classifying as conventional", verbose)
                return 0x5, None
        else:
            ops.show("  [Track association] DSRC track but no matching radar track", verbose)
            return 0x3, query.id
    else:
        if len(results) > 1:
            ops.show("  [Warning] {} vehicles within gating region of radar detection!".format(len(results)), verbose)
            # choose the closest
            sorted_results = sorted(results, key=lambda pair: len(pair[1]))
            id = sorted_results[0][0]
            ops.show("  [Track association] Associating with closest track {}".format(id), verbose)
            if sensor == Radar:
                if method == "track-to-track":
                    return 0x2, id
                elif method == "measurement-to-track":
                    return 0x6, id
            else:
                return 0x4, id
        else:
            r = results[0]
            if sensor == Radar:
                if method == "track-to-track":
                    ops.show("  [Track association] Associating with track {}".format(r[0]), verbose)
                    return 0x2, r[0]
                elif method == "measurement-to-track":
                    ops.show("  [Measurement association] Associating with track {}".format(r[0]), verbose)
                    return 0x6, r[0]
            else:
                return 0x4, r[0]
