import time

from prometheus_client import Gauge, start_http_server

from chirp_sensor.driver import Chirp, MoistureCalibration


def create_exporter():
    calibration = MoistureCalibration(dry=240, wet=750)
    sensor = Chirp(bus=1, address=0x20, calibration=calibration)

    g_moist = Gauge("chirp_moisture_raw", "Raw moisture reading")
    g_moist_pct = Gauge("chirp_moisture_percent", "Moisture percent")
    g_temp = Gauge("chirp_temperature_celsius", "Temperature in Celsius")
    g_light = Gauge("chirp_light", "Light reading (0=bright, 65535=dark)")

    def update(interval: float = 10.0):
        while True:
            r = sensor.read()
            g_moist.set(r.moisture)
            if r.moisture_percent is not None:
                g_moist_pct.set(r.moisture_percent)
            g_temp.set(r.temperature_c)
            g_light.set(r.light)
            time.sleep(interval)

    return update


exporter = None


def main():
    global exporter
    exporter = create_exporter()
    start_http_server(9100)
    exporter(10.0)


if __name__ == "__main__":
    main()
