from sensible.sensors.DSRC import DSRC


with open('C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\plots\\radar_msg', 'r') as f:
    csm = f.read()

    msg = DSRC.parse(csm)

    print(msg)
