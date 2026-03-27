from fastapi import FastAPI, HTTPException
import fastf1
import asyncio
import os
from typing import List, Dict

# -------------------------------
# FastF1 Setup
# -------------------------------
# Enable caching
CACHE_DIR = "cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache("cache")

# -------------------------------
# App Init
# -------------------------------
app = FastAPI(
    title="F1 Data API",
    description="FastAPI + FastF1 (optimized with threading)",
    version="1.0.0"
)

# -------------------------------
# Helper Functions (SYNC)
# -------------------------------
def load_race_results_sync(year: int, gp: str):
    session = fastf1.get_session(year, gp, 'R')
    session.load()
    return session.results


def load_driver_laps_sync(year: int, gp: str, driver_code: str):
    session = fastf1.get_session(year, gp, 'R')
    session.load()
    laps = session.laps.pick_drivers(driver_code)
    return laps


# -------------------------------
# Routes
# -------------------------------
@app.get("/")
async def home():
    return {"message": "F1 API running (FastAPI + FastF1)"}


@app.get("/race/{year}/{gp}")
async def get_race_results(year: int, gp: str) -> Dict:
    try:
        # Run blocking FastF1 code in separate thread
        results = await asyncio.to_thread(load_race_results_sync, year, gp)

        data: List[Dict] = []
        for _, driver in results.iterrows():
            data.append({
                "position": int(driver['Position']),
                "driver": driver['Abbreviation'],
                "team": driver['TeamName'],
                "time": str(driver['Time']) if driver['Time'] else "N/A"
            })

        return {
            "race": f"{year} {gp}",
            "results": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/driver/{year}/{gp}/{driver_code}")
async def get_driver_laps(year: int, gp: str, driver_code: str) -> Dict:
    try:
        # Run blocking FastF1 code in separate thread
        laps = await asyncio.to_thread(
            load_driver_laps_sync, year, gp, driver_code
        )

        lap_times: List[Dict] = []
        for _, lap in laps.iterrows():
            lap_times.append({
                "lap": int(lap['LapNumber']),
                "time": str(lap['LapTime'])
            })

        return {
            "driver": driver_code.upper(),
            "laps": lap_times
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Optional: Health Check
# -------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}