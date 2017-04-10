from sensible.util import ops
from sensible.sensors.radar import Radar
from sensible.sensors.DSRC import DSRC


def single_hypothesis_association(track_list, query_track, verbose=False):
    """
    Single-hypothesis track-to-track association

    Using Chi-squared tables for 4 degrees of freedom (one for each
    dimension of the state vector), for different p-values

    p = 0.05 -> 9.49
    p = 0.01 -> 13.28
    p = 0.001 -> 18.47

    Result codes
    ============
    0x1 : query_track is a radar track and association w/ DSRC failed; change type to CONVENTIONAL and send BSM.
          Associated track id is the query track id.
    0x2 : query_track is a radar track and association w/ DSRC succeeded; change type to CONNECTED and send BSM if not served
          update the track id of query_track to match that of the DSRC track
    0x3 : query_track is a DSRC track and association w/ radar failed; send BSM if not yet served
          Associated track id is the query track id.
    0x4 : query_track is a DSRC track and association w/ radar succeeded; change type of the radar track to CONNECTED
          and update radar track id to match that of query_track

    :param track_list: List of (id, track) pairs
    :param query_track: The track that is to be associated
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

        # First condition ensures the query track isn't fused with itself,
        # and the second condition ensures two radar or two DSRC tracks
        # aren't fused together
        if track_id == query_track.id or track.sensor == query_track.sensor:
            continue

        md = track.state_estimator.mahalanobis(query_track.state_estimator.state(),
                                               query_track.state_estimator.process_covariance())

        ops.show("  [Track Association] Track {} has a Mahalanobis distance of {} "
                 "to the detection".format(track_id, md), verbose)

        if md <= 9.488:
            results.append((track_id, md))

    # radar_t_stamp = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
    # radar_log_str = " [GNN] Radar msg: {},{},{},{},{}\n".format(
    #     radar_t_stamp.to_string(), radar_measurement[0], radar_measurement[2],
    #     radar_measurement[1], radar_measurement[3]
    # )
    # print(radar_log_str)

    # Association "failed"
    if len(results) == 0:
        # measurement didn't fall near any tracked vehicles, so if a radar track tentatively
        # associate as a conventional vehicle
        if query_track.sensor == Radar:
            ops.show("  [Track Association] Conventional vehicle detected", verbose)
            return 0x1, query_track.id
        else:
            ops.show("  [Track Association] DSRC track but no matching radar track", verbose)
            return 0x3, query_track.id
    else:
        if len(results) > 1:
            ops.show("  [Warning] {} vehicles within gating region of radar detection!".format(len(results)), verbose)
            # choose the closest
            sorted_results = sorted(results, key=lambda pair: len(pair[1]))
            id = sorted_results[0][0]
            ops.show("  [Track Association] Associating with track {}".format(id), verbose)
            if query_track.sensor == Radar:
                return 0x2, id
            else:
                return 0x4, id
        else:
            r = results[0]
            ops.show("  [Track Association] Associating with track {}".format(r[0]), verbose)
            # track = self._track_list[r[0]]
            # potentially fuse this with the kalman filter
            if query_track.sensor == Radar:
                return 0x2, r[0]
            else:
                return 0x4, r[0]
