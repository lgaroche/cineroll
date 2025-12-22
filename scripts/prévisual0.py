#! /usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as gpio
import picamera
from time import sleep
from PIL import Image
ledPin = 14
gpio.setmode(gpio.BCM)  # notation BCM
gpio.setup(ledPin, gpio.OUT)

camera = picamera.PiCamera()
#camera.resolution = (2592, 1944)
#camera.resolution = (1296, 972)
#camera.resolution = (1024, 768)
#camera.resolution = (720, 576)
camera.resolution = (640, 480)
decalage_H = 0.210
decalage_V = 0.230
zoom = 0.410
camera.zoom = (decalage_H,decalage_V,zoom,zoom)
camera.meter_mode = 'backlit'
#camera.meter_mode = 'matrix'
#camera.framerate = 15
camera.iso = 0
camera.brightness = 50
camera.awb_mode = 'sunlight'
#camera.awb_mode = 'incandescent'
camera.exposure_mode = 'backlight'

camera.contrast = 0
#camera.vflip = True


gpio.output(ledPin, 1)
camera.start_preview()
sleep(100)
#boucle


gpio.output(ledPin, 0)   
camera.stop_preview()
#camera.close()


