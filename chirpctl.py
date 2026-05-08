#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

import main_mqtt
import main_prom
import main_rest
from chirp_sensor.calibrator import AutoCalibrator
from chirp_sensor.config import Config, load_config
from chirp_sensor.driver import Chirp, MoistureCalibration


def load_sensor(args: argparse.Namespace) -> Chirp:
    cfg: Config = load_config()

    # CLI overrides config.toml
    bus = args.bus if args.bus is not None else cfg.bus
    address = args.address if args.address is not None else cfg.address

    dry = args.dry if args.dry is not None else cfg.dry
    wet = args.wet if args.wet is not None else cfg.wet

    calibration = None
    if dry is not None and wet is not None:
        calibration = MoistureCalibration(dry, wet)

    return Chirp(bus=bus, address=address, calibration=calibration)


def cmd_read(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    r = sensor.read()
    print(
        json.dumps(
            {
                "moisture_raw": r.moisture,
                "moisture_percent": r.moisture_percent,
                "temperature_c": r.temperature_c,
                "light": r.light,
                "timestamp": r.timestamp.isoformat(),
            },
            indent=2,
        )
    )


def cmd_moisture(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.read_moisture())


def cmd_temp(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.read_temperature_c())


def cmd_light(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.read_light())


def cmd_version(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.version)


def cmd_calibrate_dry(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.read_moisture())


def cmd_calibrate_wet(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(sensor.read_moisture())


def cmd_sleep(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    sensor.sleep()
    print("Sensor is now sleeping.")


def cmd_wake(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    sensor.wake_up()
    print("Sensor is awake.")


def cmd_address_set(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    sensor.sensor_address = args.new_addr
    print(f"Address changed to {hex(args.new_addr)}")


def cmd_debug(args: argparse.Namespace) -> None:
    sensor = load_sensor(args)
    print(f"Address: {hex(sensor.address)}")
    print(f"Version: {sensor.version}")
    print(f"Busy: {sensor._busy()}")
    print(f"Moisture (raw): {sensor.read_moisture()}")
    print(f"Temperature (C): {sensor.read_temperature_c()}")
    print(f"Light: {sensor.read_light()}")


def cmd_rest(args: argparse.Namespace) -> None:
    cfg = load_config()
    app = main_rest.create_app()

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=cfg.rest_port)


def cmd_mqtt(args: argparse.Namespace) -> None:
    main_mqtt.main()


def cmd_prom(args: argparse.Namespace) -> None:
    main_prom.main()


def cmd_calibrate_auto(args: argparse.Namespace) -> None:
    cfg = load_config()
    sensor = Chirp(bus=cfg.bus, address=cfg.address)
    cal = AutoCalibrator(sensor)
    result = cal.run()

    print("\nSuggested chirp.toml values:")
    print(f"dry = {result.dry}")
    print(f"wet = {result.wet}")

    if args.write:
        cal.write_to_toml("chirp.toml", result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chirpctl",
        description="Command-line interface for Chirp soil sensors",
    )

    # CLI overrides config.toml
    parser.add_argument("--address", type=int, help="I2C address")
    parser.add_argument("--bus", type=int, help="I2C bus number")
    parser.add_argument("--dry", type=int, help="Dry calibration value")
    parser.add_argument("--wet", type=int, help="Wet calibration value")

    sub = parser.add_subparsers(dest="command")

    # Basic reads
    sub.add_parser("read").set_defaults(func=cmd_read)
    sub.add_parser("moisture").set_defaults(func=cmd_moisture)
    sub.add_parser("temp").set_defaults(func=cmd_temp)
    sub.add_parser("light").set_defaults(func=cmd_light)
    sub.add_parser("version").set_defaults(func=cmd_version)

    # Calibration
    cal = sub.add_parser("calibrate")
    cal_sub = cal.add_subparsers(dest="cal_cmd")
    cal_sub.add_parser("dry").set_defaults(func=cmd_calibrate_dry)
    cal_sub.add_parser("wet").set_defaults(func=cmd_calibrate_wet)

    # Auto-calibration
    cal_auto = cal_sub.add_parser("auto", help="Auto-calibrate dry/wet values")
    cal_auto.add_argument(
        "--write",
        action="store_true",
        help="Write calibration values directly into chirp.toml",
    )
    cal_auto.set_defaults(func=cmd_calibrate_auto)

    # Device management
    sub.add_parser("sleep").set_defaults(func=cmd_sleep)
    sub.add_parser("wake").set_defaults(func=cmd_wake)

    addr = sub.add_parser("address")
    addr_sub = addr.add_subparsers(dest="addr_cmd")
    p = addr_sub.add_parser("set")
    p.add_argument("new_addr", type=int)
    p.set_defaults(func=cmd_address_set)

    # Diagnostics
    sub.add_parser("debug").set_defaults(func=cmd_debug)

    # Services
    sub.add_parser("rest").set_defaults(func=cmd_rest)
    sub.add_parser("mqtt").set_defaults(func=cmd_mqtt)
    sub.add_parser("prom").set_defaults(func=cmd_prom)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
