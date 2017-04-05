
def single_hypothesis_association(track_list, query_track_id):
    """
    Single-hypothesis track-to-track association

    Using Chi-squared tables for 4 degrees of freedom (one for each
    dimension of the state vector), for different p-values

    p = 0.05 -> 9.49
    p = 0.01 -> 13.28
    p = 0.001 -> 18.47

    :param track_list: List of (id, track) pairs
    :param query_track_id: The track that is to be associated
    :return: the track id of the associated track
    """
    query_track = track_list[query_track_id]

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

        md = track.state_estimator.mahalanobis(query_track.state_estimator.state(),
                                               query_track.state_estimator.process_covariance())

        print("  [DA] Track {} has a Mahalanobis distance of {} "
              "to the detection".format(track_id, md))

        if md <= 9.488:
            results.append((track_id, md))

    # radar_t_stamp = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
    # radar_log_str = " [GNN] Radar msg: {},{},{},{},{}\n".format(
    #     radar_t_stamp.to_string(), radar_measurement[0], radar_measurement[2],
    #     radar_measurement[1], radar_measurement[3]
    # )
    # print(radar_log_str)

    if len(results) == 0:
        # radar measurement didn't fall near any tracked vehicles, so tentatively
        # associate as a conventional vehicle
        print("  [DA] Conventional vehicle detected, sending BSM...")
        return query_track_id
    else:
        if len(results) > 1:
            print("  [Warning] {} vehicles within gating region of radar detection!".format(len(results)))
            # choose the closest
            sorted_results = sorted(results, key=lambda pair: len(pair[1]))
            id = sorted_results[0][0]
            print("  [DA] Associating radar detection with vehicle {}".format(id))
            return id
        else:
            r = results[0]
            print("  [DA] Associating radar detection with vehicle {}".format(r[0]))
            # track = self._track_list[r[0]]
            # potentially fuse this with the kalman filter
            return r[0]