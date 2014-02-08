#!/usr/bin/python
# Sam Bingham - PantherROV IV
# top tcp/ip communication interface
# to rabbit microcontroller
import sys
import socket
from ctypes import *
#from ansi import *
from PyQt4 import QtCore
# motor pwm command buffer indexes
# global LV, RV, LH, RV
LV = 1
RV = 2
LH = 3
RH = 4
# rabbit microcontroller address
HOST = "192.168.1.222"
PORT = 22222
# buffer size microcontroller is expecting
BUFSIZE = 8
CharArray = c_char * BUFSIZE
#buffer size to recieve data from microcontroller

#multiplier to find voltage from a to d value  = 5 / 256
#had to be declared here due to a unknown bug that wouldnt calculate it.
magic_num = 0.01953125

class ROVComm(QtCore.QObject):
	def __init__(self, parent=None):
		self.local_buffer = CharArray()
		self.reset_buf
		print("Buffer is " + str(BUFSIZE) + " bytes indexed from 0-" + str(BUFSIZE-1))
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print("Socket opened...")
		#flag for checking pc to rov connection
		self.connected = False

	def connect(self):
		if self.connected is not True:
			try:
				print("Connecting to " + HOST +":" + str(PORT) + "...")
				self.sock.connect((HOST, PORT))
				self.connected = True
				print("Connection estabished.")
				self.reset_buf
				self.send_buf
			except socket.error, msg:
				print("Socket error: " + str(msg))
		else:
			print("Unable to connect: Already connected.")
	
	def disconnect(self):
		if self.connected is True:
			self.sock.close()
			self.connected = False
			print("Connection closed.")
		else:
			print("Unable to disconnect: No connection")
	
	def send_buf(self):
		if self.connected is True:
			try:
				self.sock.send(self.local_buffer);
			except socket.error, msg:
				print("Socket error: " + str(msg))
		else:
			print("Unable to send buffer: No connection")
	
	def reset_buf(self):
		self.local_buffer[0] = chr(255)
		for i in range(1, 8):
			self.local_buffer[i] = chr(150)
		#for j in range(5, BUFSIZE):
		#	self.local_buffer[j] = chr(0)
	
	def read_temp(self):
		# might be better to recieve buffer in differnt way
		temp = -1 #disconnected return value
		if self.connected is True:
			#print "temp"
			temp_buf = self.sock.recv(1)
			if temp_buf != chr(255): #and len(temp_buf)
				#self.remote_buffer = temp_buf
				#convert to volts then to celcius'''
				temp =  (ord(temp_buf) * magic_num) / 0.056
		return temp
	'''
	@pre: ALL thruster movements sent need to be between 
		     90-210 MAX as this is the max range on the motor
		     controllers
	'''
	def move_vert(self, val):
		val = 300 - val #invert value
		self.local_buffer[LV] = chr(val)
		self.local_buffer[RV] = chr(val)
		self.send_buf()
	
	def move_horz(self, val):
		self.local_buffer[LH] = chr(val)
		self.local_buffer[RH] = chr(val)
		self.send_buf()
		
	def turn(self, val):
		if val < 150: #turn right
			self.local_buffer[RH] = chr(150)
			self.local_buffer[LH] = chr(val)
		else: #elif val > 150: #turn left
			val = 300 - val
			self.local_buffer[RH] = chr(val)
			self.local_buffer[LH] = chr(150)
		self.send_buf()
		
	def turn_backward(self, val):
		if val < 150: #turn right
			val = 300 - val #invert value
			self.local_buffer[LH] = chr(150)
			self.local_buffer[RH] = chr(val)
		else: #elif val > 150: #turn left
			self.local_buffer[LH] = chr(val)
			self.local_buffer[RH] = chr(150)
		self.send_buf()
		
	def pivot(self, val):
		val2 = 300 - val
		self.local_buffer[LH] = chr(val2)
		self.local_buffer[RH] = chr(val)
		self.send_buf()
		
	'''def roll(self, val):
		val2 = 300 - val #invert value
		self.local_buffer[LV] = chr(val)
		self.local_buffer[RV] = chr(val2)
		self.send_buf()'''
		
	#sends value of 150 which equals stop (center)
	def stop_vert(self):
		self.move_vert(150)
		
	def stop_horz(self):
		self.move_horz(150)
		
	def stop_turn(self):
		self.move_horz(150)
	
	def stop_all(self):
		self.stop_vert()
		self.stop_horz()


# only needed for test() function
def read_byte():
	b = int(raw_input())
	while (b > 255 or b < 0): 
		b = int(raw_input("INVALID INPUT - Enter value[0-255]: "))
	return b
		
def test():
	rov = ROVComm()
	print("                           |`-:_\n"\
		  "  ,----....____            |    `+.\n"\
		  " (             ````----....|___   |\n"\
		  "  \    _                      ````----....____\n"\
		  "   \    _)  UWM Panther ROV IV              ```---.._\n"\
		  "    \            Raw Communication Interface          \ \n"\
		  "  )`.\  )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.  \)`.   )\n"\
		  "-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'\n")
	print("              !! Type 'help' for command list !!\n")
	exit = 0
	while(exit == 0):
		try:
			rov.reset_buf()
			cmd = raw_input("Please enter a command: ")
			if (cmd == "exit"):
				print("Exiting...")
				exit = 1
			elif (cmd == "connect"):
				rov.connect()
			elif (cmd == "read_temp"):
				print rov.read_temp()
			elif (cmd == "disconnect"):
				rov.disconnect()
			elif (cmd == "reset_buffer"):
				print("Reseting buffer...")
				rov.reset_buf()    
			elif (cmd == "send_byte"):
				index = int(raw_input("Enter buffer index: "))
				print("Enter value [0-255]: "); val = read_byte()
				rov.local_buffer[index] = chr(val)
			elif (cmd == "send_array"):
				print("For each buffer index enter value [0-255]:") 
				for i in range(0,BUFSIZE):
					print("local_buffer['i'] = ")
					rov.local_buffer[i] = chr(read_byte())
			elif (cmd == "help"):
				print("Commands are: \n"\
					  "send_byte, send_array, reset_buffer, read_temp, "\
					  "connect, disconnect, exit \n")
			if (exit == 1 and rov.connected == True): 
				rov.disconnect()
			elif (rov.connected == True):
				rov.send_buf()
				
		except Exception, e:
			print e

if __name__ == '__main__': test()