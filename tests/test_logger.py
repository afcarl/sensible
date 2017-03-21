import time
import os


def test_track_logger():
    # Track logger
    t = time.localtime()
    log_dir = os.getcwd()
    timestamp = time.strftime('%m-%d-%Y_%H%M', t)
    p = open(os.path.join(log_dir, '..', 'logs', "trackLog_" + timestamp + ".csv"), 'wb')
    q = p
    logger_title = "TrackID,TrackState,Filtered,timestamp,xPos,yPos,xSpeed,ySpeed\n"
    q.write(logger_title)
    q.close()


if __name__ == '__main__':
    test_track_logger()
