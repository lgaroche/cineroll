from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


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


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# État global de la machine
led_state = False
counter = 0
zoom_level = 0
pan_x = 0
pan_y = 0
frame_position = 0
capture_active = False
capture_target = 0
capture_count = 0


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "led": led_state
    })


@app.get("/status")
async def get_status():
    return {
        "led": led_state,
        "zoom_level": zoom_level,
        "pan_x": pan_x,
        "pan_y": pan_y,
        "frame_position": frame_position,
        "capture_active": capture_active,
        "capture_target": capture_target,
        "capture_count": capture_count
    }


@app.post("/led")
async def toggle_led():
    global led_state
    led_state = not led_state
    return {"led": led_state}


@app.post("/advance")
async def advance_frames(action: FrameAction):
    global frame_position
    frame_position += action.frames
    return {"frame_position": frame_position}


@app.post("/rewind")
async def rewind_frames(action: FrameAction):
    global frame_position
    frame_position -= action.frames
    return {"frame_position": frame_position}


@app.post("/zoom")
async def adjust_zoom(action: ZoomAction):
    global zoom_level
    zoom_level += action.direction
    return {"zoom_level": zoom_level}


@app.post("/pan")
async def adjust_pan(action: PanAction):
    global pan_x, pan_y
    pan_x += action.x
    pan_y += action.y
    return {"pan_x": pan_x, "pan_y": pan_y}


@app.post("/capture/start")
async def start_capture(action: CaptureStart):
    global capture_active, capture_target, capture_count
    capture_active = True
    capture_target = action.frames
    capture_count = 0
    return {
        "capture_active": capture_active,
        "capture_target": capture_target,
        "capture_count": capture_count
    }


@app.post("/capture/stop")
async def stop_capture():
    global capture_active
    capture_active = False
    return {"capture_active": capture_active}


@app.get("/image")
async def get_image():
    global counter
    counter += 1
    return {"image": f"https://picsum.photos/536/354?counter={counter}"}
