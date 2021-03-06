import sys
import socket
import argparse
import threading
import logging
import json 
import yaml 
import psycopg2
from struct import pack, unpack
from datetime import datetime

FIRST_PART = pack('i', 0)
END_PART = pack('<i', 82)

logging.basicConfig(filename='developer_info.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

conf = yaml.load(open('application.yml'), Loader=yaml.BaseLoader)
parser = argparse.ArgumentParser(description = "This is the server for the multithreaded socket.")
parser.add_argument('--host', metavar = 'host', type = str, nargs = '?', default = socket.gethostname())
parser.add_argument('--port', metavar = 'port', type = int, nargs = '?', default = 8443)
args = parser.parse_args()


print("Running the server on: {} and port: {}".format(args.host, args.port))

sck = socket.socket()
sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def get_vehicles():
	connection = psycopg2.connect(user = conf['db']['user'], password = conf['db']['password'], host = conf['db']['host'], port = conf['db']['port'], database = conf['db']['database'])
	cursor = connection.cursor()
	cursor.execute('SELECT id, internal_code FROM vehicles ORDER BY id ASC')
	x = cursor.fetchall()
	if(connection):
		cursor.close()
		connection.close()
	return x

def on_new_client(client, connection):
	ip = connection[0]
	port = connection[1]
	logging.info("The new connection was made from IP: {}, and port: {}!".format(ip, port))
	while True:
		msg = client.recv(1024)
		strMsg = msg.strip().decode('utf-8', 'ignore')	
		if len(strMsg) > 0:
			logging.info("Clean data: {}".format(msg))
			handle_message(client, strMsg)
	client.close()
	logging.info("The client from ip: {}, and port: {}, has gracefully disconnected!".format(ip, port))

def handle_message(client, strMsg):
	try:
		index = strMsg.find("{")
		tmp = strMsg[index:]
		loaded_json = json.loads(tmp)
		operation = loaded_json['OPERATION']
		session_id = loaded_json['SESSION']
		if operation == "CONNECT":
			#device_id = loaded_json['PARAMETER']['DSNO']
			connectionReply(client, session_id)
		elif operation == "KEEPALIVE":
			reply = json.dumps({"MODULE":"CERTIFICATE","OPERATION":"KEEPALIVE","SESSION":session_id})
			client.send(reply.encode('utf-8'))
	except Exception as e:
		logging.error("Failed fam!: {}".format(e))
		print("Failed fam!: {}".format(e))

def connectionReply(client, session_id):
	payloadJson = json.dumps({"MODULE":"CERTIFICATE","OPERATION":"CONNECT","RESPONSE":{"DEVTYPE":1,"ERRORCAUSE":"","ERRORCODE":0,"MASKCMD":1,"PRO":"1.0.4","VCODE":""},"SESSION":session_id})
	payload = str(payloadJson).replace(" ", "")
	pLength = sys.getsizeof(payload)
	midPart = pack('>i', pLength)
	completeMessage = FIRST_PART + midPart + END_PART + payload.encode('utf-8')
	print(completeMessage)
	client.send(completeMessage)
	#payloadJsonBinary = json.dumps({"MODULE":"CONFIGMODEL","OPERATION":"SET","PARAMETER":{"MDVR":{"KEYS":{"GV":1},"PGDSM":{"PGPS":{"EN":1}},"PIS":{"PC041245T":{"GU":{"EN":1,"IT":5}}},"PSI":{"CG":{"UEM":0}}}},"SESSION":session_id})
	#payloadBinary = str(payloadJsonBinary).replace(" ", "")
	#pLengthBinary = sys.getsizeof(payloadBinary)
	#midPartBinary = pack('>i', pLengthBinary)
	#completeMessageBinary = FIRST_PART +  midPartBinary + END_PART
	#client.send(completeMessageBinary.encode('utf-8'))

try: 
	sck.bind((args.host, args.port))
	sck.listen(5)
	#records = get_vehicles()
except Exception as e:
	raise SystemExit("We could not bind the server on host: {} to port: {}, because: {}".format(args.host, args.port, e))

while True:
	try: 
		client, ip = sck.accept()
		threading._start_new_thread(on_new_client,(client, ip))
	except KeyboardInterrupt:
		print("Gracefully shutting down the server!")
		sys.exit()
	except Exception as e:
		print("Well I did not anticipate this: {}".format(e))

sck.close()


def handleRegularReports(self, data):
    try:
      connection = psycopg2.connect(user = conf['db']['user'], password = conf['db']['password'], host = conf['db']['host'], port = conf['db']['port'], database = conf['db']['database'])
      cursor = connection.cursor()
      size = unpack('>i', data[0:12][4:8])[0] + 12
      splitedData = list(self.chunked(size, data))
      for msg in splitedData:  
        if msg[12:13] == b'\x00':
          gpsStatus = 'ok'
        elif msg[12:13] == b'\x01':
          gpsStatus ='bad'
        else:
          gpsStatus = 'no gps'
        longitude = unpack('>i',msg[16:20])[0]/1000000
        latitude = unpack('>i',msg[20:24])[0]/1000000
        speed =  unpack('>i',msg[24:28])[0]/100
        angle =  unpack('>i',msg[28:32])[0]/100
        altitude =  unpack('>i',msg[32:36])[0]
        date = datetime.strptime(msg[36:].decode('utf-8', 'ignore').rstrip('\x00') + "-05:00", '%Y%m%d%H%M%S%f%z').strftime('%Y/%m/%d %H:%M:%S:%f %z')
        finalValues = {'gpsStatus': gpsStatus, 'latitude': latitude, 'longitude': longitude, 'speed': speed, 'angle': angle, 'altitude': altitude, 'date': date}      
        print(finalValues)
        #self.createOnDb(connection, cursor, finalValues)
    except (Exception, psycopg2.Error) as error:
      if(connection):
        logging.error("Failed to insert record into mobile table: {}".format(error))
    finally:
      if(connection):
        cursor.close()
        connection.close()
    
  def chunked(self, size, source):
    for i in range(0, len(source), size):
      yield source[i:i+size]