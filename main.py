import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from hardware import controller, MOCK_MODE


# Modèles Pydantic
class FrameAction(BaseModel):
    frames: int = 1


class ZoomAction(BaseModel):
    direction: int  # 1 ou -1


class PanAction(BaseModel):
    x: int = 0
    y: int = 0


class CaptureStart(BaseModel):
    frames: int


# Configuration
# En mode mock, utiliser un répertoire local
if MOCK_MODE:
    CAPTURE_DIR = "./capture"
else:
    CAPTURE_DIR = "/mnt/Super8/capture"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    controller.initialize()
    yield
    controller.cleanup()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "led": controller.led_state,
        "mock_mode": MOCK_MODE
    })


@app.get("/status")
async def get_status():
    return controller.get_status()


@app.post("/led")
async def toggle_led():
    state = controller.led_toggle()
    return {"led": state}


@app.post("/advance")
async def advance_frames(action: FrameAction):
    await controller.advance_frames(action.frames)
    return {"frame_position": controller.frame_position}


@app.post("/rewind")
async def rewind_frames(action: FrameAction):
    await controller.rewind_frames(action.frames)
    return {"frame_position": controller.frame_position}


@app.post("/zoom")
async def adjust_zoom(action: ZoomAction):
    zoom = controller.set_zoom(action.direction)
    return {"zoom_level": zoom}


@app.post("/pan")
async def adjust_pan(action: PanAction):
    pan_h, pan_v = controller.set_pan(action.x, action.y)
    return {"pan_x": pan_h, "pan_y": pan_v}


@app.post("/capture/start")
async def start_capture(action: CaptureStart):
    # Lancer la capture en tâche de fond
    loop = asyncio.get_event_loop()
    loop.create_task(
        controller.start_capture(action.frames, CAPTURE_DIR)
    )
    # Petite pause pour laisser la tâche démarrer
    await asyncio.sleep(0.1)
    return controller.get_status()


@app.post("/capture/stop")
async def stop_capture():
    controller.stop_capture()
    return {"capture_active": controller.capture_active}


@app.get("/image")
async def get_image():
    if MOCK_MODE:
        # Mode développement: inclure tous les paramètres pour forcer le rechargement
        # quand frame, zoom ou pan changent
        return {
            "image": f"https://picsum.photos/536/354?frame={controller.frame_position}"
                     f"&zoom={controller.zoom_level}&pan={controller.pan_position}"
        }
    else:
        # Mode réel: retourne l'image caméra
        frame = controller.get_preview_frame()
        return Response(content=frame, media_type="image/jpeg")
