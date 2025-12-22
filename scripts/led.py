#! /usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as gpio
from time import sleep
ledPin = 14   # alim LED
#ledPin = 8
gpio.setmode(gpio.BCM)  # notation BCM

gpio.setup(ledPin, gpio.OUT)  # pin configurée en sortie

while True:
    gpio.output(ledPin, 1)
    print("un coup ça marche")
    sleep(1)
    #gpio.output(ledPin, 0)
    print("un coup ça marche pas")
    sleep(1)
    