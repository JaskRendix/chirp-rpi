#!/usr/bin/env python3
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from chirp_sensor.config import Config, load_config
from chirp_sensor.driver import Chirp, MoistureCalibration


def create_app() -> FastAPI:
    cfg: Config = load_config()

    calibration = (
        MoistureCalibration(cfg.dry, cfg.wet)
        if cfg.dry is not None and cfg.wet is not None
        else None
    )

    sensor = Chirp(
        bus=cfg.bus,
        address=cfg.address,
        calibration=calibration,
    )

    app = FastAPI()

    class ReadingModel(BaseModel):
        moisture: int
        moisture_percent: float | None
        temperature_c: float
        light: int
        timestamp: str

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/read", response_model=ReadingModel)
    def read_all() -> ReadingModel:
        r = sensor.read()
        return ReadingModel(
            moisture=r.moisture,
            moisture_percent=r.moisture_percent,
            temperature_c=r.temperature_c,
            light=r.light,
            timestamp=r.timestamp.isoformat(),
        )

    @app.get("/moisture")
    def moisture() -> dict[str, float | int | None]:
        r = sensor.read()
        return {"moisture": r.moisture, "percent": r.moisture_percent}

    @app.get("/temperature")
    def temperature() -> dict[str, float]:
        r = sensor.read()
        return {"temperature_c": r.temperature_c}

    @app.get("/light")
    def light() -> dict[str, int]:
        r = sensor.read()
        return {"light": r.light}

    return app


app: FastAPI | None = None


def main() -> None:
    global app
    app = create_app()


if __name__ == "__main__":
    main()
    import uvicorn

    cfg = load_config()
    uvicorn.run(app, host="0.0.0.0", port=cfg.rest_port)
