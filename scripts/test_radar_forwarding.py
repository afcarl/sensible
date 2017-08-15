import socket
import time 
import cPickle as pickle


if __name__ == '__main__':

	run_for = 10  # 10 seconds
	msg_len = 300

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# open connection to incoming messages
	try:
		sock.bind(("localhost", 4200))
		sock.setblocking(0)
	except socket.error as e:
		print(e)

	start = time.time()

	while time.time() - start < run_for:
		try:
			msg, address = sock.recvfrom(msg_len)
			msg_ = pickle.loads(msg)
			print(msg_)
		except socket.error as err:
			continue

	sock.close()