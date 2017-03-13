class TrackState:
    """Enumerated type for track states."""
    CONFIRMED = 1
    UNCONFIRMED = 2
    ZOMBIE = 3
    DEAD = 4

    @staticmethod
    def as_string(state):
        if state == TrackState.CONFIRMED:
            return "CONFIRMED"
        elif state == TrackState.UNCONFIRMED:
            return "UNCONFIRMED"
        elif state == TrackState.ZOMBIE:
            return "ZOMBIE"
        elif state == TrackState.DEAD:
            return "DEAD"
        else:
            raise ValueError("Unknown TrackState {}".format(state))

