from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import subprocess
import concurrent.futures
import os

RADIATION_BIN = os.path.join(os.path.dirname(__file__), "radiation_calc")
DEFAULT_WORKERS = 16  

app = FastAPI(title="Radiation Grid API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RadiationGridRequest(BaseModel):
    year: int
    month: int
    day: int
    altitude: float
    g_parameter: float
    goes_proton: float
    lat_step: float = Field(default=1.0, gt=0.0)
    lon_step: float = Field(default=1.0, gt=0.0)
    max_workers: int = Field(default=DEFAULT_WORKERS, ge=1, le=256)

def run_radiation_calc(year: int, month: int, day: int,
                       lat: float, lon: float,
                       altitude: float, g: float, goes: float) -> float:
    
    cmd = [
        RADIATION_BIN,
        str(year), str(month), str(day),
        f"{lat:.6f}", f"{lon:.6f}",
        f"{altitude}", f"{g}", f"{goes}",
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/radiation_grid")
def radiation_grid(req: RadiationGridRequest):
    
    height = int(180 / req.lat_step)
    width = int(360 / req.lon_step)

    lat_vals = [90.0 - y * req.lat_step for y in range(height)]
    lon_vals = [-180.0 + x * req.lon_step for x in range(width)]

    values = [0.0] * (width * height)

    
    tasks = []
    for y, lat in enumerate(lat_vals):
        base = y * width
        for x, lon in enumerate(lon_vals):
            idx = base + x
            tasks.append((idx, lat, lon))

    def worker(t):
        idx, lat, lon = t
        v = run_radiation_calc(
            req.year, req.month, req.day,
            lat, lon,
            req.altitude, req.g_parameter, req.goes_proton
        )
        return idx, v

    
    with concurrent.futures.ThreadPoolExecutor(max_workers=req.max_workers) as ex:
        for idx, v in ex.map(worker, tasks):
            values[idx] = v

    min_v = min(values)
    max_v = max(values)

    return {
        "width": width,
        "height": height,
        "latStep": req.lat_step,
        "lonStep": req.lon_step,
        "values": values,
        "min": min_v,
        "max": max_v,
    }
