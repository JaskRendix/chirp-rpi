# Chirp‑RPI — Modern Python Driver and Tools for the Chirp Soil Sensor

Chirp‑RPI is a modern Python 3.12+ driver and toolkit for the **Chirp capacitive soil‑moisture sensor**, which also measures temperature and ambient light.  
It provides a typed driver, calibration utilities, structured readings, a command‑line interface, and optional integrations such as MQTT, Prometheus, and a REST API.

This project is a modernized and extended rewrite of the original driver by @ageir:  
[https://github.com/ageir/chirp-rpi](https://github.com/ageir/chirp-rpi)

Hardware design by Albertas Mickėnas (Catnip Electronics):  
[https://github.com/Miceuz/i2c-moisture-sensor](https://github.com/Miceuz/i2c-moisture-sensor)  
[https://www.tindie.com/products/miceuz/i2c-soil-moisture-sensor/](https://www.tindie.com/products/miceuz/i2c-soil-moisture-sensor/)

---

## Features

### Core driver
- Raw moisture (capacitance)
- Moisture percentage (with calibration)
- Temperature in Celsius
- Light measurement (0 = bright, 65535 = dark)
- Timestamped readings
- I²C address read/write
- Deep‑sleep and wake support
- Context‑manager support
- Busy‑flag polling interval (`busy_sleep`)
- Read timeout with retry (`read_timeout_s`)

### Additional tools
- SoilAgent for drying‑rate estimation and moisture‑level prediction
- Auto‑calibration helper with stability detection
- MQTT publisher for home automation
- Prometheus exporter for monitoring dashboards
- FastAPI REST server for remote access
- `chirpctl` command‑line interface (argparse)

---

## Installation

Stable installation:

```bash
pip install chirp-rpi   # not yet published to PyPI
```

Development installation:

```bash
git clone https://github.com/<yourrepo>/chirp-rpi
cd chirp-rpi
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

Requirements:
- Python 3.12+
- I²C enabled on the host system
- smbus2

---

## Configuration (`chirp.toml`)

All tools load configuration from a local `chirp.toml` file:

```toml
bus = 1
address = 0x20

dry = 240
wet = 750

busy_sleep = 0.01
read_timeout_s = 1.0

mqtt_host = "localhost"
mqtt_port = 1883
mqtt_base = "home/chirp/basil"

prom_port = 9100
rest_port = 8000
```

CLI flags override values in the file:

```bash
chirpctl --address 0x21 read
```

The auto‑calibration helper can update this file automatically:

```bash
chirpctl calibrate auto --write
```

---

## Command‑Line Interface (`chirpctl`)

The CLI provides quick access to sensor readings, calibration, debugging, and running services.

### Basic usage

```bash
chirpctl read
chirpctl moisture
chirpctl temp
chirpctl light
chirpctl version
```

### Calibration

```bash
chirpctl calibrate dry
chirpctl calibrate wet
chirpctl calibrate auto
chirpctl calibrate auto --write
```

### Device management

```bash
chirpctl sleep
chirpctl wake
chirpctl address set 0x21
```

### Diagnostics

```bash
chirpctl debug
```

### Running services

```bash
chirpctl rest
chirpctl mqtt
chirpctl prom
```

Global options:

```bash
--address 0x20
--bus 1
--dry 240 --wet 750
```

---

## Calibration

To convert raw capacitance into moisture percentage, calibration is required.

### Manual procedure
1. Let the sensor stabilize in dry air; record the lowest raw value.  
2. Submerge the sensing area in water; record the highest raw value.  
3. Use these values to create a calibration object.

### Example

```python
from chirp_sensor.driver import MoistureCalibration, Chirp

cal = MoistureCalibration(dry=240, wet=750)
sensor = Chirp(address=0x20, calibration=cal)
```

### Auto‑calibration

Chirp‑RPI includes an interactive auto‑calibration helper:

```bash
chirpctl calibrate auto
```

The tool:

- samples moisture readings  
- detects stability automatically  
- computes dry and wet calibration points  
- optionally writes them to `chirp.toml`:

```bash
chirpctl calibrate auto --write
```

---

## Python API

### MoistureCalibration

```python
MoistureCalibration(dry: int, wet: int)
```

Convert raw moisture values into percentages:

```python
pct = cal.to_percent(raw_value)
```

---

### ChirpReading

Returned by `sensor.read()`:

```python
@dataclass
class ChirpReading:
    moisture: int
    moisture_percent: Optional[float]
    temperature_c: float
    light: int
    timestamp: datetime
```

---

### Chirp Driver

```python
from chirp_sensor.driver import Chirp, MoistureCalibration

sensor = Chirp(
    bus=1,
    address=0x20,
    calibration=MoistureCalibration(240, 750),
    busy_sleep=0.01,
    read_timeout_s=1.0,
)
```

#### Read all sensors

```python
reading = sensor.read()
```

#### Read individual values

```python
sensor.read_moisture()
sensor.read_temperature_c()
sensor.read_light()
```

#### Change I²C address

```python
sensor.sensor_address = 0x21
```

#### Context manager

```python
with Chirp(address=0x20) as sensor:
    print(sensor.read())
```

---

## SoilAgent

Tracks moisture history and estimates:

- Drying rate (% per hour)
- Hours until a target moisture level is reached

Example:

```python
from chirp_sensor.agent import SoilAgent
```

---

## MQTT Publisher

Publishes sensor state as JSON every 30 seconds.

Run:

```bash
python main_mqtt.py
```

---

## Prometheus Exporter

Exports metrics on port 9100.

Run:

```bash
python main_prom.py
```

---

## REST API (FastAPI)

Run:

```bash
python main_rest.py
```

Endpoints:

- `/read`
- `/moisture`
- `/temperature`
- `/light`
- `/health`

---

## Testing

Run the full test suite:

```bash
pytest -q
```

Includes:

- Driver tests  
- Calibration tests  
- Auto‑calibration tests  
- Error‑condition tests  
- Integration tests for MQTT, REST, Prometheus  
- CLI tests  

---

## Project Structure

```
chirp-rpi/
│
├── chirp_sensor/
│   ├── driver.py
│   ├── agent.py
│   ├── calibrator.py
│   ├── config.py
│
├── chirpctl.py
├── main_agent.py
├── main_mqtt.py
├── main_prom.py
├── main_rest.py
│
├── chirp.toml
├── tests/
├── pyproject.toml
└── README.md
```

---

## License

MIT License.  
Hardware design © Catnip Electronics.

---

## Credits

This project builds on earlier work by:

- Albertas Mickėnas (hardware)
- @ageir — original Python driver  
- Jasper Wallace and Daniel Tamm — early implementations

Modernized and extended by the current maintainers.
