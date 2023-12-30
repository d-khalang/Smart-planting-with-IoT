# Smart-planting-with-IoT
An IoT ecosystem for urban farming
# SkyFarming IoT Project

## Overview
SkyFarming is an innovative IoT project focused on hydroponic vertical farming in skyscrapers. The project aims to utilize IoT devices to monitor and control various aspects of plant growth in different units across different levels of a tower.

## Project Structure
The project is structured with a central device and resource registry known as the "Catalog." This registry is crucial for managing and organizing data related to the system and its devices.

### Catalog
The catalog is implemented in the script `catalog_registery.py`. It serves as the heart of the system, responsible for recording and organizing data related to devices and resources. The collected data is stored in a JSON file named `catalog.json`, which will ultimately serve as the project's database.

## Components
Each plant unit is equipped wiht two main types of IoT devices:

1. **Sensor Devices:** These devices are responsible for collecting data related to the environment, such as temperature, PH, nutrition, and light conditions.

2. **Actuator Devices:** These devices control physical components, enabling automation of processes critical to plant growth.

## Current Stage
At this stage of development, the catalog has been implemented, and it successfully writes all system and device-related data to the `catalog.json` file.

## Getting Started
Loading ...


## Future Development
The project is in its early stages, with planned enhancements including the integration of sensor and actuator devices for comprehensive monitoring and control of plant units.

## Contributing
Contributions are welcome! If you're interested in contributing to SkyFarming, please open an issue or submit a pull request.
