from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

import fastf1
import asyncio
import os

# -------------------------------
# Setup cache (safe)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# -------------------------------
# App init
# -------------------------------
app = FastAPI()

# Static + Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS (optional but safe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Frontend Route
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------
# FastF1 helpers
# -------------------------------
def load_race_results_sync(year: int, gp: str):
    session = fastf1.get_session(year, gp, 'R')
    session.load()
    return session.results

def load_driver_laps_sync(year: int, gp: str, driver_code: str):
    session = fastf1.get_session(year, gp, 'R')
    session.load()
    return session.laps.pick_drivers(driver_code)

# -------------------------------
# API routes
# -------------------------------
@app.get("/race/{year}/{gp}")
async def get_race_results(year: int, gp: str):
    try:
        results = await asyncio.to_thread(load_race_results_sync, year, gp)

        data = []
        for _, driver in results.iterrows():
            data.append({
                "position": int(driver['Position']),
                "driver": driver['Abbreviation'],
                "team": driver['TeamName'],
                "time": str(driver['Time']) if driver['Time'] else "N/A"
            })

        return {"race": f"{year} {gp}", "results": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/driver/{year}/{gp}/{driver_code}")
async def get_driver_laps(year: int, gp: str, driver_code: str):
    try:
        laps = await asyncio.to_thread(
            load_driver_laps_sync, year, gp, driver_code
        )

        lap_times = []
        for _, lap in laps.iterrows():
            lap_times.append({
                "lap": int(lap['LapNumber']),
                "time": str(lap['LapTime'])
            })

        return {"driver": driver_code.upper(), "laps": lap_times}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))