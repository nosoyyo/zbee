# Installation

for python3 only

# Usage

## start zworker
python3 zbee.py
python3 wxbee.py

## start pipes
context = zmq.Context()
pipe_sender = context.socket(zmq.PUSH) 
pipe_sender.connect('tcp://192.168.1.112:5557') 