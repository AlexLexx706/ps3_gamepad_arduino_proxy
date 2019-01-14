# -*- coding: utf-8 -*-
import evdev
from evdev import InputDevice
import time
import threading
import math
import struct
import serial
import sys

# stick type
EV_ABS = 3

# stiks
ABS_X = 0
ABS_Y = 1
ABS_Z = 2
ABS_RX = 3
ABS_RY = 4
ABS_RZ = 5


# 1. read devices
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
dev_path = '/dev/input/event22'

# 2. select wrileles device
for device in devices:
    if device.name == 'Wireless Controller':
        dev_path = device.path
        print('Use device:%s' % (device.name, ))
        break
else:
    print('Use default device')

# 3. get gamegad device
gamepad = InputDevice(dev_path)
caps = gamepad.capabilities()

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# print(caps)

# 4. get gamepad state
sticks = {
    d[0]: {
        'value': d[1].value,
        'mean': d[1].value,
        'min': d[1].min,
        'max': d[1].max} for d in caps[EV_ABS]}

stop_flag = False
w_dedband = 0.1  # 10%
v_dedband = 0.1  # 10%
w_max = 90       # angular speed grad/sec
v_max = 180      # gain 0-255

programm_in_used = False
prog_w = 0.0
prog_v = 0.0


def read_port():
    while not stop_flag:
        s = ser.read()
        # sys.stdout.write(s)


def update_proxy():
    while not stop_flag:
        if not programm_in_used:
            # 1. create angular speed
            w = (sticks[ABS_X]['value'] - sticks[ABS_X]['min']) / float(
                sticks[ABS_X]['max'] - sticks[ABS_X]['min'])
            w = (-(w - 0.5) / 0.5)

            if math.fabs(w) < w_dedband:
                w = 0.0
            else:
                val = (math.fabs(w) - w_dedband) / (1. - w_dedband)
                w = val if w > 0.0 else -val
                w = w * w_max

            # 2. create linear speed
            v = (sticks[ABS_Y]['value'] - sticks[ABS_Y]['min']) / float(
                sticks[ABS_Y]['max'] - sticks[ABS_Y]['min'])
            v = (-(v - 0.5) / 0.5)

            if math.fabs(v) < v_dedband:
                v = 0.0
            else:
                val = (math.fabs(v) - v_dedband) / (1. - v_dedband)
                v = val if v > 0.0 else -val
                # print(v)
                v = v * v_max
        else:
            w = prog_w
            v = prog_v

        # create packet for arduino
        s = b'A%sB' % (struct.pack('<ff', w, v), )
        ser.write(s)
        # print(s, len(s))
        print(w, v)
        time.sleep(0.02)


stop_programm = False
min_sleep = 0.1


def my_sleep(sec):
    for i in range(int(sec / min_sleep)):
        time.sleep(min_sleep)
        if stop_programm:
            print
            raise RuntimeError(1)


def program():
    global prog_v, prog_w
    global programm_in_used

    programm_in_used = True
    prog_v = 0.0
    prog_w = 0.0

    try:
        while not stop_programm:
            # 1. move
            prog_v = 80
            my_sleep(1)

            # 2. stop
            prog_v = 0.0
            my_sleep(1)

            # 3. ratate
            prog_w = 45
            my_sleep(4)

            # 4. stop
            prog_w = 0.0
            my_sleep(1)
    except (RuntimeError, KeyboardInterrupt):
        pass

    prog_v = 0.0
    prog_w = 0.0


thread = threading.Thread(target=update_proxy)
thread.start()

thread2 = threading.Thread(target=read_port)
thread2.start()

# start programm
try:
    raw_input('press key for start programm')
    thread3 = threading.Thread(target=program)
    thread3.start()
    raw_input('press key for stop programm')
    if 0:
        # start_time = time.time()
        # count = 0
        for event in gamepad.read_loop():
            if event.type == EV_ABS:
                sticks[event.code]['value'] = event.value
            # press button
            elif event.type == 1:
                if event.code == 304:
                    print('key press:%s' % (event, ))
except:
    pass
finally:
    stop_programm = True
    prog_v = 0.0
    prog_w = 0.0
    time.sleep(0.1)
    stop_flag = True
