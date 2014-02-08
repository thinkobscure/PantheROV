PantheROV
---------------

Initial commit is my old code for PantheROV IV (circa 2008). 

**firmware\\** contains dynamic-c code for on board Rabbit microcontroller

**topside\\** contains python code for computer client to read data and control the ROV with a USB PS2 style joystick
- *rov\_main\_cmd.py* is the main software to control and communicate with the ROV
- *rov_comm.py* is the communication lib for ROV control, includes standalone testing interface

Running topside client interface requires python ctypes, PyQT4, and numeric

