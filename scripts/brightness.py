import time
import picamera

with picamera.PiCamera() as camera:
    camera.start_preview()
    try:
        for i in range(-50,50):
            camera.annotate_text = "contrast: %s " % i
            camera.contrast = i
            #camera.brightness = i
            time.sleep(0.2)
    finally:
        camera.stop_preview()