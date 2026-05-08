# Chirp‑RPI — Modern Python Driver and Tools for the Chirp Soil Sensor

Chirp‑RPI is a modern Python 3.12+ driver and toolkit for the **Chirp capacitive soil‑moisture sensor**, which also measures temperature and ambient light.  
It provides a clean, typed driver, calibration utilities, structured readings, a command‑line interface, and optional integrations such as MQTT, Prometheus, and a REST API.

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

### Additional tools
- SoilAgent for drying‑rate estimation and moisture‑level prediction
- MQTT publisher for home automation
- Prometheus exporter for monitoring dashboards
- FastAPI REST server for remote access
- **`chirpctl` command‑line interface (argparse)**

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

## Command‑Line Interface (`chirpctl`)

The project includes a lightweight argparse‑based CLI for quick sensor access, debugging, calibration, and running services.

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
--address 0x20   # I2C address
--bus 1          # I2C bus
--dry 240 --wet 750   # calibration values
```

---

## Calibration

To convert raw capacitance into moisture percentage, calibration is required.

### Procedure
1. Let the sensor stabilize in dry air; record the lowest raw value.
2. Submerge the sensing area in water; record the highest raw value.
3. Create a calibration object using these values.
4. Use the calibration in the driver or CLI.

### Example

```python
from chirp_sensor.driver import MoistureCalibration, Chirp

cal = MoistureCalibration(dry=240, wet=750)
sensor = Chirp(address=0x20, calibration=cal)
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
)
```

#### Read all sensors

```python
reading = sensor.read()
print(reading.moisture, reading.moisture_percent, reading.temperature_c, reading.light)
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

The SoilAgent tracks moisture history and estimates:

- Drying rate (% per hour)
- Hours until a target moisture level is reached

Example:

```python
from chirp_sensor.agent import SoilAgent
from chirp_sensor.driver import Chirp, MoistureCalibration

sensor = Chirp(address=0x20, calibration=MoistureCalibration(240, 750))
agent = SoilAgent(sensor)

reading = agent.sample()
rate = agent.estimate_drying_rate()
eta = agent.predict_hours_until(30.0)
```

---

## MQTT Publisher

Publishes sensor state as JSON every 30 seconds.

Run:

```bash
python main_mqtt.py
```

Example payload:

```json
{
  "moisture_raw": 255,
  "moisture_percent": 2.9,
  "temperature_c": 25.8,
  "light": 8603,
  "timestamp": "2026-05-08T15:55:00"
}
```

---

## Prometheus Exporter

Exports metrics on port 9100.

Run:

```bash
python main_prom.py
```

Metrics include:

- chirp_moisture_raw
- chirp_moisture_percent
- chirp_temperature_celsius
- chirp_light

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

Example:

```bash
curl http://localhost:8000/read
```

---

## Testing

Run the full test suite:

```bash
pytest -q
```

GitHub Actions automatically runs:

- Driver tests  
- Calibration tests  
- Edge‑case tests  
- Failure‑mode tests  
- Integration tests for MQTT, REST, Prometheus  
- **CLI tests**

---

## Project Structure

```
chirp-rpi/
│
├── chirp_sensor/
│   ├── driver.py
│   ├── agent.py
│
├── chirpctl.py
├── main_agent.py
├── main_mqtt.py
├── main_prom.py
├── main_rest.py
│
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
  [https://github.com/ageir/chirp-rpi](https://github.com/ageir/chirp-rpi)
- Jasper Wallace and Daniel Tamm — early implementations

Modernized and extended by the current maintainers.
