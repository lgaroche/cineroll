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
freq = 3000 # frequence pwm
pwm = gpio.PWM(stepPin,freq)


#réglage camera
#camera.resolution = (2592, 1944)
#camera.resolution = (1296, 972)
#camera.resolution = (1024, 768)
camera.resolution = (720, 576)
#camera.resolution = (640, 480)
decalage_H = 0.210
decalage_V = 0.235
zoom = 0.410
camera.zoom = (decalage_H,decalage_V,zoom,zoom)
camera.meter_mode = 'backlit'
#camera.meter_mode = 'matrix'
#camera.framerate = 15
#camera.iso = 000
#camera.brightness = 52
brightness = 52
#camera.awb_mode = 'incandescent'
#camera.awb_mode = 'tungsten'
camera.awb_mode = 'sunlight'
camera.exposure_mode = 'backlight'
camera.contrast = 0
#camera.vflip = True

repertoire = '/mnt/Super8/capture/'
#repertoire  = 'test'


def captureImage(x):
    #sleep(1)

    camera.brightness = brightness
    fichier = repertoire + 'test/%04d.jpg' %n
    camera.capture(fichier, quality=100)

 
    print(fichier)

    return (x+1)

gpio.add_event_detect (capturePin,gpio.FALLING, bouncetime=500)
#gpio.add_event_callback (capturePin, callback=captureImage)


gpio.output(ledPin,1)
sleep(2)

# initialisation variables
nbImages = 3*18*60
#nbImages = 180
# n = n° première image
n = 3240
nbImages+=n


gpio.output(enablePin, 0)
gpio.output(dirPin, 0) # 0=AV
#pwm.ChangeFrequency(float(freq))


#boucle
while n < nbImages:
    pwm.start(50) # rapport cyclique = 50%
    #sleep(1)
    if gpio.event_detected(capturePin):
        n=captureImage(n)
    #print("ça tourne " + str(n))

gpio.output(enablePin, 1)   # désactivation pilote
gpio.output(ledPin,0)
pwm.stop()