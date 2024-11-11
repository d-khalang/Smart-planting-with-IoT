# Smart Planting with IoT - SkyFarming Project

## Overview
SkyFarming is an innovative IoT project dedicated to hydroponic vertical farming in urban skyscrapers. Leveraging IoT technology, it facilitates efficient monitoring and control of various aspects of plant growth across different levels of a tower.

![image_2024-03-11_17-08-34](https://github.com/d-khalang/Smart-planting-with-IoT/assets/77327582/83bdcbb1-c426-468d-9a80-6c059e0fed77)


## Project Structure
The project consists of several interconnected components:

### Catalog
- **Files:** `catalog_registry.py`, `catalog.json`
- **Description:** The catalog serves as the device and service registry, managed by `catalog_registry.py`. It reads, updates, and writes information to `catalog.json`, functioning as a small-scale database. `catalog_registry.py` provides a web service with methods for GET, POST, and PUT requests, enabling device connectors to register themselves and their devices. It also features a scheduler to remove outdated device registrations.

### Device Connectors
- **Files:** `device_connector.py`, `device_connector_act.py`, `DC_instancer.py`, `DC_instancer_act.py`, `sensors.py`, `setting_act.json`, `setting_sen.json`
- **Description:** Device connectors are responsible for managing sensor and actuator devices for each plant unit. `sensors.py` simulates sensor data, which is published to corresponding MQTT topics by `device_connector.py` and `device_connector_act.py`. `DC_instancer.py` and `DC_instancer_act.py` dynamically create device connectors based on configurations in `setting_act.json` and `setting_sen.json`. These connectors register plant and device information with the catalog.

### Control Units
- **Files:** `CU_instancer.py`, `MyMQTT2.py`, `control_unit.py`
- **Description:** Control units manage plant conditions by subscribing to plant topics, receiving sensing information, and taking corrective actions if necessary. `CU_instancer.py` dynamically creates control units, optimizing their number based on the active plants and levels. They interact with the catalog to retrieve plant information and intervene when sensor data deviates from optimal conditions.

### ThingSpeak Integration
- **File:** `adaptor.py`
- **Description:** This component integrates with ThingSpeak for data storage and visualization. `adaptor.py` subscribes to plant topics, receives sensing information via MQTT, and writes data to ThingSpeak channels. It also creates ThingSpeak channels as needed.

### User Awareness
- **Files:** `operator_control.py`, `interface.py`, `telegbot.py`
- **Description:** User awareness is facilitated through three sections:
  - `operator_control.py` manages information for the operator interface and Telegram bot, gathering data on available ThingSpeak channels, sensor and actuator statuses.
  - `interface.py` creates a web interface using Flask, displaying plant information, ThingSpeak graphs, and enabling operator interaction with actuators.
  - `telegbot.py` is a Telegram bot allowing end-users to monitor plant status, view sensing data, and control devices.


## Future Development
The project lays the groundwork for comprehensive monitoring and control of plant units. 
Future enhancements may include scalability improvements, real device integration, and advanced data analytics.

