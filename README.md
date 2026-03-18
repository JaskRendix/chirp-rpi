# Chirp Sensor – Python Driver Documentation

## Overview
Chirp is a capacitive soil‑moisture sensor with onboard temperature and light measurement. It is open hardware designed by Albertas Mickėnas (Catnip Electronics).

Hardware and reference designs:
- https://github.com/Miceuz/i2c-moisture-sensor/
- https://www.tindie.com/products/miceuz/i2c-soil-moisture-sensor/

This Python driver provides an I²C interface to the sensor. The implementation is based on work by @ageir and contributors, with earlier versions by Jasper Wallace and Daniel Tamm:
- https://github.com/ageir/chirp-rpi/
- https://github.com/JasperWallace/chirp-graphite/blob/master/chirp.py

---

## Features
- Trigger function for enabled sensors  
- Moisture as raw capacitance or percent (requires calibration)  
- Temperature in Celsius, Fahrenheit, or Kelvin  
- Temperature offset  
- Timestamps for all measurements  
- I²C address change support  
- Deep‑sleep mode  
- Calibration helper class  

---

## Calibration
Moisture percentage requires calibrated minimum and maximum raw values. Without calibration, `moisture_percent` may fall outside 0–100%.

### Procedure
1. Read raw moisture in dry air; record the lowest stable value.  
2. Read raw moisture with the sensor submerged; record the highest stable value.  
3. Use these values as `dry` and `wet` in `MoistureCalibration`.  
4. Calibrate in the environment where the sensor will operate.

### Example
```python
from chirp_sensor.driver import MoistureCalibration, Chirp

cal = MoistureCalibration(dry=240, wet=750)
sensor = Chirp(address=0x20, calibration=cal)
```

---

## Class Reference

### Chirp
```
Chirp(
    bus=1,
    address=0x20,
    calibration=None,
    read_temp=True,
    read_moist=True,
    read_light=True,
)
```

### Arguments
- **bus** (int): I²C bus number  
- **address** (int): I²C address (3–119)  
- **calibration** (MoistureCalibration | None): Calibration object  
- **read_temp** (bool): Enable temperature measurement  
- **read_moist** (bool): Enable moisture measurement  
- **read_light** (bool): Enable light measurement  

---

## MoistureCalibration
```
MoistureCalibration(dry: int, wet: int)
```

- **dry**: Raw moisture value in dry air  
- **wet**: Raw moisture value in water  

---

## Attributes
- **address**: I²C address  
- **busy_sleep**: Delay while waiting for measurement (default 0.01 s)  
- **moisture**: Raw moisture value  
- **moisture_percent**: Moisture percentage (requires calibration)  
- **temperature_c**: Temperature in Celsius  
- **light**: Light value  
- **timestamp**: Timestamp of the last reading  
- **read_temp**, **read_moist**, **read_light**: Enabled sensors  
- **calibration**: MoistureCalibration instance  

---

## Methods
- **read()** — Read all enabled sensors and return a structured result  
- **read_moisture()** — Read moisture only  
- **read_temperature_c()** — Read temperature in Celsius  
- **read_light()** — Read light value  
- **reset()** — Reset the sensor  
- **sleep()** — Enter deep‑sleep mode  
- **wake_up(wake_time=1)** — Wake the sensor  
- **sensor_address (property)** — Get or set I²C address  

---

## Properties
- **version** — Firmware version  
- **busy** — Sensor busy state  
- **sensor_address** — I²C address (read/write)  
- **moisture_percent** — Moisture percentage (requires calibration)  

---

## Examples

### Basic usage
```python
from chirp_sensor.driver import Chirp, MoistureCalibration

cal = MoistureCalibration(dry=240, wet=750)
sensor = Chirp(address=0x20, calibration=cal)

r = sensor.read()
print(r.moisture, r.moisture_percent, r.temperature_c, r.light)
```

### Change I²C address
```python
sensor = Chirp(address=0x20)
sensor.sensor_address = 0x21
```

### Continuous measurement
```python
import time
from chirp_sensor.driver import Chirp, MoistureCalibration

cal = MoistureCalibration(dry=240, wet=750)
sensor = Chirp(address=0x20, calibration=cal)

while True:
    r = sensor.read()
    print(r.moisture, r.moisture_percent, r.temperature_c, r.light)
    time.sleep(1)
```
