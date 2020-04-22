import socket
import argparse
import time

parser = argparse.ArgumentParser(description="This is the client")
parser.add_argument('--timeout', metavar = 'timeout', type = float, nargs = '?', default = 0.5)
parser.add_argument('--host', metavar='host', type=str, nargs='?', default=socket.gethostname())
parser.add_argument('--port', metavar = 'port', type = int, nargs = '?', default = 8443)
args = parser.parse_args()

print(f"Connecting to server: {args.host} on port: {args.port}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
	try:
		sck.connect((args.host, args.port))
	except Exception as e:
		raise SystemExit(f"We have failed to connect to host: {args.host} on port: {args.port}, because: {e}")

	while True:
		msg = b'\x08\x00\x00\x00\x00\x00\x01\xfbR\x00\x00\x00{"MODULE":"CERTIFICATE","OPERATION":"CONNECT","PARAMETER":{"AUTOCAR":"prueba","AUTONO":"0","CARNUM":"","CHANNEL":16,"CID":572537376,"CNAME":"CUSTOMER_04.1519","DEVCLASS":4,"DEVNAME":"MDVR","DEVTYPE":1,"DLIP":[{"LIP":"0.0.0.0","MT":"eth0"}],"DLP":[80,9006],"DSNO":"00980001E4","EID":"APSI18_80","EV":"V1.1","FSV":0,"LINENO":"","MAC":[{"IMAC":"00:00:00:00:00:00","MT":"eth0"}],"MODE":1,"MTYPE":79,"NET":2,"PRO":"1.0.5","STYPE":74,"TSE":1,"UNAME":"","UNO":""},"SESSION":"185a10f3-c84b-45f4-947e-d24dab8728ba"}\n'
		sck.sendall(msg)
		if msg =='exit':
			print("Client is saying goodbye!")
			break
		data = sck.recv(1024)
		print("The server's response was: {}".format(data))
		time.sleep(args.timeout)