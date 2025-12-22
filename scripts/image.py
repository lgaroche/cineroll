import picamera
from time import sleep
from PIL import Image
import RPi.GPIO as gpio

ledPin = 14   # alim LED
gpio.setmode(gpio.BCM)  # notation BCM
gpio.setup(ledPin, gpio.OUT)  # pin configurée en sortie

camera = picamera.PiCamera()
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
camera.iso = 000
camera.brightness = 50
camera.awb_mode = 'sunlight'
#camera.awb_mode = 'incandescent'
#camera.awb_mode = 'tungsten'
camera.exposure_mode = 'backlight'
camera.contrast = 0
#camera.vflip = True



#camera.start_preview()
#boucle
gpio.output(ledPin, 1)
sleep(1)

fichier = 'previsual.jpg'
camera.capture(fichier,quality=100)
print(fichier)


#image = '/mnt/Super8/39.jpg'
img = Image.open(fichier)
img.show()
#img1 = img.resize((720, 576)).show()


sleep(2)
#gpio.output(ledPin, 0)

img.close()   
camera.stop_preview()
camera.close()