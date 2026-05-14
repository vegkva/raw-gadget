# WIP threaded USB emulation on single UDC (mouse and keyboard)

Python websockets server captures keyboard and mouse of the user -> writes HID data into two files on remote system -> mouse_keyboard.c listens on these files continuously
Running two threads.

Code is not production ready and not very good written (got a lot of help from ChatGPT), might crash any time I guess... Not tested on real UDC yet

Not sure how the raw gadget module responds to so much traffic on one UDC. Maybe better to use modes to switch between mouse and keyboard..?