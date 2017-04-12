import time
import os
import socket
import sys

if __name__ == '__main__':

	if not len(sys.argv) == 4:
		print('  [ERROR] Must provide 3 arguments')
		exit(1)

	ip_address = sys.argv[1]
	port = int(sys.argv[2])
	ttr = int(sys.argv[3])

	t = time.localtime()
	log_dir = os.getcwd()
	timestamp = time.strftime('%m-%d-%Y_%H%M', t)
	msg_len = 300

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	try:
		sock.bind((ip_address, port))
		sock.setblocking(0)
	except socket.error as e:
		print(e)

	log_name = os.path.join(log_dir, 'logs', "radarLog_" + timestamp + ".txt")

	start = time.time()

	with open(log_name, 'wb') as log:
		while(time.time() - start < ttr):
			try:
				msg, address = sock.recvfrom(msg_len)
				log.write(msg)
			except socket.error as e:
				continue
		sock.close()

	print("Finished logging radar, log saved at: {}".format(log_name))
