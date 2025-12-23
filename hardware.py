"""
Module de contrôle matériel pour la machine Super8 Cineroll.
Gère le GPIO (LED, moteur pas-à-pas) et la caméra (picamera2).
"""

import asyncio
import io
import os
from typing import Optional
from datetime import datetime

# Détection du mode mock (hors Raspberry Pi)
MOCK_MODE = False
try:
    import RPi.GPIO as gpio
    from picamera2 import Picamera2
except ImportError:
    MOCK_MODE = True
    gpio = None
    Picamera2 = None

print(f"[DEBUG] MOCK_MODE = {MOCK_MODE}")


class Super8Controller:
    """Contrôleur non-bloquant pour la machine Super8."""

    # Configuration GPIO (BCM)
    STEP_PIN = 18      # PWM moteur
    DIR_PIN = 7        # Direction (0=AV, 1=AR)
    ENABLE_PIN = 25    # Activer pilote moteur
    CAPTURE_PIN = 17   # Capteur rotation
    LED_PIN = 14       # Éclairage LED
    MS1_PIN = 9        # Microstepping
    MS2_PIN = 10
    MS3_PIN = 11

    # Configuration caméra
    RESOLUTION = (720, 576)
    DEFAULT_ZOOM = 0.410
    DEFAULT_PAN_H = 0.210
    DEFAULT_PAN_V = 0.235

    # Configuration moteur
    PWM_FREQ = 3000    # Fréquence PWM

    def __init__(self):
        self._led_state = False
        self._zoom = self.DEFAULT_ZOOM
        self._pan_h = self.DEFAULT_PAN_H
        self._pan_v = self.DEFAULT_PAN_V
        self._frame_position = 0

        # État capture
        self._capture_active = False
        self._capture_target = 0
        self._capture_count = 0
        self._stop_requested = False
        self._capture_task: Optional[asyncio.Task] = None
        self._last_error: Optional[str] = None

        # Hardware
        self._pwm = None
        self._camera = None
        self._sensor_size = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialise le GPIO et la caméra."""
        if MOCK_MODE:
            print("[MOCK] Hardware initialization skipped")
            self._initialized = True
            return

        # Configuration GPIO
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)

        gpio.setup(self.ENABLE_PIN, gpio.OUT)
        gpio.setup(self.STEP_PIN, gpio.OUT)
        gpio.setup(self.CAPTURE_PIN, gpio.IN)
        gpio.setup(self.DIR_PIN, gpio.OUT)
        gpio.setup(self.LED_PIN, gpio.OUT)
        gpio.setup(self.MS1_PIN, gpio.OUT)
        gpio.setup(self.MS2_PIN, gpio.OUT)
        gpio.setup(self.MS3_PIN, gpio.OUT)

        # Microstepping configuration
        gpio.output(self.MS1_PIN, 0)
        gpio.output(self.MS2_PIN, 1)
        gpio.output(self.MS3_PIN, 1)

        # Désactiver le moteur au démarrage
        gpio.output(self.ENABLE_PIN, 1)
        gpio.output(self.LED_PIN, 0)

        # PWM
        self._pwm = gpio.PWM(self.STEP_PIN, self.PWM_FREQ)

        # Détection événement capteur
        # D'abord supprimer toute détection existante (au cas où le programme a crashé)
        try:
            gpio.remove_event_detect(self.CAPTURE_PIN)
        except Exception:
            pass  # Ignorer si pas de détection existante

        try:
            gpio.add_event_detect(
                self.CAPTURE_PIN,
                gpio.FALLING,
                bouncetime=500
            )
        except RuntimeError as e:
            print(f"[WARNING] Failed to add edge detection: {e}")
            print("[WARNING] Frame detection may not work properly")

        # Caméra picamera2
        self._camera = Picamera2()
        config = self._camera.create_still_configuration(
            main={"size": self.RESOLUTION}
        )
        self._camera.configure(config)
        self._camera.start()

        # Récupérer la taille du capteur pour ScalerCrop
        self._sensor_size = self._camera.camera_properties['PixelArraySize']
        self._update_camera_crop()

        self._initialized = True
        print("Hardware initialized successfully")

    def cleanup(self) -> None:
        """Libère les ressources GPIO et caméra."""
        if MOCK_MODE:
            print("[MOCK] Hardware cleanup skipped")
            return

        if self._capture_active:
            self.stop_capture()

        if self._pwm:
            self._pwm.stop()

        if self._camera:
            self._camera.stop()
            self._camera.close()

        gpio.output(self.LED_PIN, 0)
        gpio.output(self.ENABLE_PIN, 1)
        gpio.cleanup()

        self._initialized = False
        print("Hardware cleaned up")

    # =========== LED ===========

    def led_on(self) -> None:
        """Allume la LED."""
        self._led_state = True
        if not MOCK_MODE:
            gpio.output(self.LED_PIN, 1)

    def led_off(self) -> None:
        """Éteint la LED."""
        self._led_state = False
        if not MOCK_MODE:
            gpio.output(self.LED_PIN, 0)

    def led_toggle(self) -> bool:
        """Bascule l'état de la LED. Retourne le nouvel état."""
        if self._led_state:
            self.led_off()
        else:
            self.led_on()
        return self._led_state

    @property
    def led_state(self) -> bool:
        return self._led_state

    # =========== MOTEUR ===========

    async def advance_frames(self, n: int) -> int:
        """
        Avance de n images. Retourne le nombre d'images avancées.
        Non-bloquant grâce à asyncio.
        """
        if MOCK_MODE:
            self._frame_position += n
            await asyncio.sleep(0.1 * n)  # Simulation
            return n

        count = 0
        gpio.output(self.DIR_PIN, 0)  # Direction avant
        gpio.output(self.ENABLE_PIN, 0)  # Activer moteur
        self._pwm.start(50)

        try:
            while count < n:
                if gpio.event_detected(self.CAPTURE_PIN):
                    count += 1
                    self._frame_position += 1
                await asyncio.sleep(0.01)
        finally:
            self._pwm.stop()
            gpio.output(self.ENABLE_PIN, 1)

        return count

    async def rewind_frames(self, n: int) -> int:
        """
        Recule de n images. Retourne le nombre d'images reculées.
        """
        if MOCK_MODE:
            self._frame_position -= n
            await asyncio.sleep(0.1 * n)
            return n

        count = 0
        gpio.output(self.DIR_PIN, 1)  # Direction arrière
        gpio.output(self.ENABLE_PIN, 0)
        self._pwm.start(50)

        try:
            while count < n:
                if gpio.event_detected(self.CAPTURE_PIN):
                    count += 1
                    self._frame_position -= 1
                await asyncio.sleep(0.01)
        finally:
            self._pwm.stop()
            gpio.output(self.ENABLE_PIN, 1)

        return count

    @property
    def frame_position(self) -> int:
        return self._frame_position

    # =========== CAMÉRA ===========

    def _update_camera_crop(self) -> None:
        """Met à jour le ScalerCrop de la caméra selon zoom/pan."""
        if MOCK_MODE or not self._camera:
            return

        sensor_w, sensor_h = self._sensor_size

        # Calculer la taille de la zone de crop
        crop_w = int(sensor_w * self._zoom)
        crop_h = int(sensor_h * self._zoom)

        # Calculer la position (pan)
        max_x = sensor_w - crop_w
        max_y = sensor_h - crop_h
        crop_x = int(self._pan_h * max_x)
        crop_y = int(self._pan_v * max_y)

        # Appliquer le crop
        self._camera.set_controls({
            "ScalerCrop": (crop_x, crop_y, crop_w, crop_h)
        })

    def set_zoom(self, direction: int) -> float:
        """
        Ajuste le zoom. direction: 1 pour zoom in, -1 pour zoom out.
        Retourne le nouveau niveau de zoom.
        """
        # Plus petit = plus zoomé
        self._zoom += direction * -0.01
        self._zoom = max(0.1, min(1.0, self._zoom))  # Limiter entre 0.1 et 1.0
        self._update_camera_crop()
        return self._zoom

    def set_pan(self, delta_x: int, delta_y: int) -> tuple[float, float]:
        """
        Ajuste le pan. Retourne (pan_h, pan_v).
        """
        self._pan_h += delta_x * 0.01
        self._pan_v += delta_y * 0.01
        self._pan_h = max(0.0, min(1.0, self._pan_h))
        self._pan_v = max(0.0, min(1.0, self._pan_v))
        self._update_camera_crop()
        return (self._pan_h, self._pan_v)

    @property
    def zoom_level(self) -> float:
        return self._zoom

    @property
    def pan_position(self) -> tuple[float, float]:
        return (self._pan_h, self._pan_v)

    def get_preview_frame(self) -> bytes:
        """Capture une image preview et retourne les bytes JPEG."""
        if MOCK_MODE:
            # Retourne une image placeholder vide
            return b''

        # Capture en mémoire
        stream = io.BytesIO()
        self._camera.capture_file(stream, format='jpeg')
        stream.seek(0)
        return stream.read()

    def capture_image(self, filepath: str) -> None:
        """Capture une image et la sauvegarde."""
        if MOCK_MODE:
            print(f"[MOCK] Capture image: {filepath}")
            return

        self._camera.capture_file(filepath)

    # =========== CAPTURE SÉQUENCE ===========

    async def start_capture(self, n_frames: int, output_dir: str) -> None:
        """
        Démarre une séquence de capture de n_frames images.
        Sauvegarde dans output_dir avec format %04d.jpg.
        """
        if self._capture_active:
            return

        self._capture_active = True
        self._capture_target = n_frames
        self._capture_count = 0
        self._stop_requested = False
        self._last_error = None

        try:
            # Créer le répertoire si nécessaire
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            self._last_error = f"Erreur création répertoire: {e}"
            self._capture_active = False
            print(f"[ERROR] {self._last_error}")
            return

        # Allumer LED
        self.led_on()

        if MOCK_MODE:
            # Simulation de capture - 5 secondes par image pour debug
            while self._capture_count < n_frames and not self._stop_requested:
                # Simuler le temps de capture (5 secondes)
                # Diviser en petits intervalles pour permettre l'arrêt d'urgence
                for _ in range(50):  # 50 x 0.1s = 5 secondes
                    if self._stop_requested:
                        break
                    await asyncio.sleep(0.1)
                if not self._stop_requested:
                    self._capture_count += 1
                    self._frame_position += 1
                    print(f"[MOCK] Captured frame {self._capture_count}/{n_frames}")
        else:
            gpio.output(self.DIR_PIN, 0)  # Direction avant
            gpio.output(self.ENABLE_PIN, 0)
            self._pwm.start(50)

            try:
                while self._capture_count < n_frames and not self._stop_requested:
                    if gpio.event_detected(self.CAPTURE_PIN):
                        # Capturer l'image
                        filename = os.path.join(
                            output_dir,
                            f"{self._capture_count + 1:04d}.jpg"
                        )
                        self.capture_image(filename)
                        self._capture_count += 1
                        self._frame_position += 1
                    await asyncio.sleep(0.01)
            finally:
                self._pwm.stop()
                gpio.output(self.ENABLE_PIN, 1)

        self._capture_active = False

    def stop_capture(self) -> None:
        """Arrêt d'urgence de la capture."""
        self._stop_requested = True
        self._capture_active = False  # Désactiver immédiatement pour l'UI

    @property
    def capture_active(self) -> bool:
        return self._capture_active

    @property
    def capture_target(self) -> int:
        return self._capture_target

    @property
    def capture_count(self) -> int:
        return self._capture_count

    # =========== STATUS ===========

    def get_status(self) -> dict:
        """Retourne l'état complet de la machine."""
        return {
            "led": self._led_state,
            "zoom_level": self._zoom,
            "pan_x": self._pan_h,
            "pan_y": self._pan_v,
            "frame_position": self._frame_position,
            "capture_active": self._capture_active,
            "capture_target": self._capture_target,
            "capture_count": self._capture_count,
            "mock_mode": MOCK_MODE,
            "error": self._last_error,
        }

    def clear_error(self) -> None:
        """Efface la dernière erreur."""
        self._last_error = None


# Singleton global
controller = Super8Controller()
