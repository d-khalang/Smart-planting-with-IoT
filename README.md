# Smart Planting with IoT - SkyFarming Project

## Overview
SkyFarming is an innovative IoT project dedicated to hydroponic vertical farming in urban skyscrapers. The project leverages IoT devices to monitor and control various aspects of plant growth across different levels of a tower.

## Project Structure
The project is organized around a central device and resource registry referred to as the "Catalog." This registry plays a crucial role in managing and organizing data related to the system and its devices.

### Catalog
The catalog is implemented in the script `catalog_registery.py`. Serving as the core of the system, it records and organizes data related to devices and resources. The collected data is stored in a JSON file named `catalog.json`, intended to be the project's database.

### Device Connectors
The `Device_connectors` directory now includes additional scripts:

1. **`device_connector.py`:** In its current stage, this script registers all devices to the catalog. In the next stage, it will be responsible for gathering sensor data and communicating it to other parts of the system.

2. **`DC_instancer.py`:** This script instantiates device connectors according to the device connector IDs specified in `setting.json`.

3. **`MyMQTT.py`:** A utility class that simplifies the process of creating MQTT publishers and subscribers. It utilizes methods from the `paho_mqtt` library.

4. **`sensors.py`:** This script emulates sensor data. Currently, it includes a temperature sensor, and additional sensors can be added in future developments.

5. **`setting.json`:** This JSON file contains information about the broker, topic, and device connector IDs.

### Control Units
On progress

## Components
Each plant unit is equipped with two main types of IoT devices:

1. **Sensor Devices:** Responsible for collecting data related to the environment, including temperature, pH, nutrition, and light conditions.

2. **Actuator Devices:** Control physical components, enabling automation of processes critical to plant growth.

## Current Stage
At this development stage, the catalog and device connector scripts have been implemented. The catalog writes data to the `catalog.json` file, and the device connector registers devices to the catalog.
The `device_connector.py` script has also been updated to create a publisher using `MyMQTT` and a sensor using `sensors.py`. It publishes the data generated by the sensor.

## Getting Started
Loading ...

## Future Development
The project is in its early stages, with planned enhancements that include the integration of sensor and actuator devices for comprehensive monitoring and control of plant units.