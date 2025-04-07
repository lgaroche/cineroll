from typing import Union
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


class CameraAction(BaseModel):
    zoom: Union[int, None] = None
    x_pan: Union[int, None] = None
    y_pan: Union[int, None] = None


app = FastAPI()
templates = Jinja2Templates(directory="templates")

led = False
counter = 0


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "led": led
    })


@app.post("/led")
async def led():
    global led
    led = not led
    return {"led": led}


@app.post("/camera")
async def camera(action: CameraAction):
    print(action)
    return {}


@app.get("/image")
async def image(request: Request):
    global counter
    counter += 1
    return {"image": f"https://picsum.photos/536/354?counter={counter}"}
