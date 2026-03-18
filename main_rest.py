from fastapi import FastAPI
from pydantic import BaseModel

from chirp_sensor.driver import Chirp, MoistureCalibration


def create_app() -> FastAPI:
    app = FastAPI()

    calibration = MoistureCalibration(dry=240, wet=750)
    sensor = Chirp(bus=1, address=0x20, calibration=calibration)

    class ReadingModel(BaseModel):
        moisture: int
        moisture_percent: float | None
        temperature_c: float
        light: int
        timestamp: str

    @app.get("/read", response_model=ReadingModel)
    def read_all():
        r = sensor.read()
        return ReadingModel(
            moisture=r.moisture,
            moisture_percent=r.moisture_percent,
            temperature_c=r.temperature_c,
            light=r.light,
            timestamp=r.timestamp.isoformat(),
        )

    @app.get("/moisture")
    def moisture():
        r = sensor.read()
        return {"moisture": r.moisture, "percent": r.moisture_percent}

    @app.get("/temperature")
    def temperature():
        r = sensor.read()
        return {"temperature_c": r.temperature_c}

    @app.get("/light")
    def light():
        r = sensor.read()
        return {"light": r.light}

    return app


app = None


def main():
    global app
    app = create_app()


if __name__ == "__main__":
    main()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
