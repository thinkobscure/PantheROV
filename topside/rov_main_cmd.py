#!/usr/bin/env python
# Sam Bingham - PantherROV IV
# ROV Control Module and mostly terminal based UI 
# * joystick uses pygames c_type wrapper for SDL to process input
# * rov_comm.ROVComm() for communication to the ROV
# joystick usage - call process_input() in an event loop
# tempature usage - call read_temp() in an event loop
# Pan-tilt Cam 192.168.1.22
# Front Cam 192.168.1.23
# Rear Cam 192.168.20

from SDL import * 
from ansi import * # wrapper for ANSI terminal functions
from PyQt4 import QtCore, QtGui
from Numeric import zeros
import rov_comm

# GLOBALS #
debug = True
# max and min values returned from sdl_joystick
AXIS_MAX = 32767
AXIS_MIN = -32768
# rov movements mapped to joystick axes id's for easy reading
VERT = 3
HORZ = 1
TURN = 0
PIVOT = 2
# rov actions mapped to joystick button id's for easy reading
STOP_ALL = 1
FINE_CONTROL  = 0
CONNECT = 9
DISCONNECT = 8

class ROVControl(QtCore.QObject):
	def __init__(self, parent=None):
		#move(18,1)
		#clear_line()
		SDL_Init(SDL_INIT_JOYSTICK)
		self.comm = rov_comm.ROVComm()
		self.temp = -1 #holds previous value of tempature
		self.temp_timer = QtCore.QTimer()
		self.joystick = SDL_JoystickOpen(0)
		self.joystick_timer = QtCore.QTimer()
		print("Initialized Joystick...")#: " + str(SDL_JoystickName(joystick)))
		self.fine_control = False
		self.num_axes = SDL_JoystickNumAxes(self.joystick)
		self.num_buttons = SDL_JoystickNumButtons(self.joystick)
		print("Axes: " + str(self.num_axes) + " Buttons: " + str(self.num_buttons))
		# stores previous values of the axes and buttons
		# creates array of zeros with size of num_
		self.axis_val = zeros(self.num_axes)
		self.button_val = zeros(self.num_buttons)
		# intitalizes axis_val with custom center (stop)
		for i in range(0,self.num_axes):
			self.axis_val[i] =  150

	def print_input(self, which, val=None):
		print(which + "\t " + str(val))
		
	# returns converted val for rov_comm
	# @post: all movement values returned must be within range of 90-210
	def normalize_by_1(self, val):
		val = int(val / (AXIS_MAX/60))
		if val < 0: #negative movement
			val = (val+1) 
		return (150+val)

	def normalize_by_2(self, val):
		val = int(val / (AXIS_MAX/30))
		if val > 0: #positive movement
			val = val - (val % 2)
		elif val < 0: #negative movement
			val = (val+1) * -1
			val = int(val - (val % 2)) * -1
		return (150+val)
		
	def normalize_by_5(self, val):
		val = int(val / (AXIS_MAX/10)) * 5 # dividing by 6 gives full range 90-210
		if val > 0: #positive movement
			val = val - (val % 5)
		elif val < 0: #negative movement
			val = (val+1) * -1
			val = int(val - (val % 5)) * -1
		return (150+val)
		
	def normalize_by_10(self, val):
		val = int(val / (AXIS_MAX/5)) * 10 # dividing by 6 gives full range 90-210
		if val > 0: #positive movement
			val = val - (val % 10)
		elif val < 0: #negative movement
			val = (val+1) * -1
			val = int(val - (val % 10)) * -1
		return (150+val)
		
	def normalize_pivot(self, val):
		if val > 150:
			n_val = int((val - 150) / 2)
			return (n_val + 150)
		elif val < 150:
			n_val = int((150 - val) / 2)
			return (150 - n_val)
		else:
			return 150
			
	def print_temp(self):
		#temp = -1
		temp = self.comm.read_temp()
		if temp is not -1:
			#move(15,1)
			#clear_line()
			#move(15,25)
			print BOLD + WHITE + '\t\t\tTemp = ' + RED + '%.1f' %temp \
			+ 'C ' + WHITE + '=' + RED + ' %.1f' %(1.8*temp+32) + 'F' + RESET
				  
	def process_input(self):
		if self.joystick is False: pass
		#self.print_temp()
		prefix = "\t\t\t" + BOLD + "* " + RESET
		SDL_JoystickUpdate()

		for a in range(0, self.num_axes):
			if self.fine_control is True:
				# divide movement value by 2 to limit movement and normalize 
				# to more percise value
				move_val = self.normalize_by_5((SDL_JoystickGetAxis(self.joystick, a)/2))
			else:
				move_val = self.normalize_by_10(SDL_JoystickGetAxis(self.joystick, a))
			if self.axis_val[a] is not move_val:
				self.axis_val[a] = move_val
				#move(16,1)
				#clear_line()
				#move(16,1)
				if a is VERT:
					if debug is True: print prefix + "move vert: " + str(move_val)
					self.comm.move_vert(move_val)
				elif a is HORZ:
					if self.axis_val[TURN] is 150:
						if debug is True: print prefix + "move horz: " + str(move_val)
						self.comm.move_horz(move_val)
				elif a is TURN:
					if self.axis_val[HORZ] < 150:
						if debug is True: print prefix + "turn: " + str(move_val)
						self.comm.turn(move_val)
					elif self.axis_val[HORZ] > 150:
						if debug is True: print prefix + "turn backward: " + str(move_val)
						self.comm.turn_backward(move_val)
				elif a is PIVOT:
					p_move_val = self.normalize_pivot(move_val)
					if debug is True: print prefix + "pivot: " + str(p_move_val) 
					self.comm.pivot(p_move_val)
	
		for b in range(0, self.num_buttons):
			changed = SDL_JoystickGetButton(self.joystick, b)
			if changed is not self.button_val[b]:
				self.button_val[b] = changed
				if self.button_val[b] is 1:
					#move(16,1)
					#clear_line()
					#move(16,1)
					if b is STOP_ALL or b is 6 or b is 7:
						if debug is True: print prefix + "'stop all' button pressed"
						self.comm.stop_all()
					elif b is CONNECT:
						if debug is True: print prefix + "'connect' button pressed"
						self.comm.connect()
					elif b is DISCONNECT:
						if debug is True: print prefix + "'disconnect' button pressed"
						self.comm.disconnect()
						sys.exit()
					elif b is FINE_CONTROL or b is 4 or b is 5:
						if debug is True: print prefix + "'fine_control' button pressed"
						self.fine_control = not self.fine_control
						print "Fine Control: " + str(self.fine_control)
					#clear_down()

class ROVControlThread(QtCore.QThread, ROVControl):
	def __init__(self, parent=None):
		QtCore.QThread.__init__(self, parent)
		ROVControl.__init__(self, parent=None)
		QtCore.QObject.connect(self.joystick_timer, QtCore.SIGNAL("timeout()"), self.process_input)
		QtCore.QObject.connect(self.temp_timer, QtCore.SIGNAL("timeout()"), self.print_temp)
		
	def run(self):
		self.joystick_timer.start(20)
		self.temp_timer.start(500)
		self.exec_()
		
if __name__ == "__main__":
	clear()
	#moveHome()
	move(1,1)
	print( BOLD + YELLOW +
		  " _   ___      ____  __ _ _                  _           \n"\
		  "| | | \ \    / /  \/  (_) |_ __ ____ _ _  _| |_____ ___ \n"\
		  "| |_| |\ \/\/ /| |\/| | | \ V  V / _` | || | / / -_) -_)\n"\
		  " \___/  \_/\_/ |_|  |_|_|_|\_/\_/\__,_|\_,_|_\_\___\___| \n"\
		  + CYAN + 
		  " _____            _   _          _____   ______      __  _______      __\n"\
		  "|  __ \          | | | |        |  __ \ / __ \ \    / / |_   _\ \    / /\n"\
		  "| |__) |_ _ _ __ | |_| |__   ___| |__) | |  | \ \  / /    | |  \ \  / / \n"\
		  "|  ___/ _` | '_ \| __| '_ \ / _ \  _  /| |  | |\ \/ /     | |   \ \/ /  \n"\
		  "| |  | (_| | | | | |_| | | |  __/ | \ \| |__| | \  /     _| |_   \  /   \n"\
		  "|_|   \__,_|_| |_|\__|_| |_|\___|_|  \_\\\____/   \/     |_____|   \/    \n\n"\
		  + BLUE + 
		  " )`.  )`.  )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.   )`.\n"\
		  "'   -'   -'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   `-'   \n"\
		  + RESET)

	app = QtGui.QApplication(['PantherROV Controller'])
	# add GLWI and UWM logos!
	text = QtGui.QLabel('\n\n\tUWM PantherROV IV\t\n\n')
	pantherov = ROVControlThread()
	pantherov.start()
	text.show()
	app.exec_()
