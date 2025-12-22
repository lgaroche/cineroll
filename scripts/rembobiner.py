#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as gpio
from time import sleep
import picamera
camera = picamera.PiCamera()

stepPin = 18  # broche PWM
dirPin = 7
enablePin = 25
capturePin = 17   # capteur tour
ledPin = 14   # alim LED
ms1 = 9
ms2 = 10
ms3 = 11

gpio.setmode(gpio.BCM)  # notation BCM
gpio.setup(enablePin, gpio.OUT)
gpio.setup(stepPin, gpio.OUT)
gpio.setup(capturePin, gpio.IN)
gpio.setup(enablePin, gpio.OUT)
gpio.setup(dirPin, gpio.OUT)
gpio.setup(ledPin, gpio.OUT)
gpio.setup(ms1, gpio.OUT)
gpio.setup(ms2, gpio.OUT)
gpio.setup(ms3, gpio.OUT)

gpio.output(ms1,0)
gpio.output(ms2,1)
gpio.output(ms3,1)
freq = 8000 # frequence pwm
pwm = gpio.PWM(stepPin,freq)

# initialisation variables

gpio.add_event_detect (capturePin,gpio.FALLING, bouncetime=1000)


#pwm.ChangeFrequency(float(freq))
camera.resolution = (720, 576)
camera.meter_mode = 'backlit'
camera.awb_mode = 'sunlight'
#camera.awb_mode = 'tungsten'
camera.contrast = -15

camera.start_preview()
gpio.output(ledPin, 1)
gpio.output(enablePin, 0)

gpio.output(dirPin, 0) # 0=AV
nbImages = 300

n = 0

#boucle
while n < nbImages:
    pwm.start(50) # rapport cyclique = 50%
    #sleep(1)
    if gpio.event_detected(capturePin):
        #n=captureImage(n)
        print(n)
        n=n+1
    #print("ça tourne " + str(n))

gpio.output(enablePin, 1)   # désactivation pilote
#gpio.output(ledPin,0)
pwm.stop()
camera.stop_preview()

camera.close()