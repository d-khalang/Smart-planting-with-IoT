from device_connector import Device_connector
import json
import time

if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    plantConfigFileName = "devices_configuration.json"
    settingFile = "setting.json"


    # with open(plantConfigFileName) as fp:
    #     plantConfig = json.load(fp)
    
    
    # Information needed for creating an Mqtt client
    with open(settingFile) as fp:
        setting = json.load(fp)
    ## DCID_dict -> device connectors' ID and corresponding plant configuration 
    baseClientID, broker, port , DCID_dict = setting["clientID"], setting["broker"], setting["port"], setting["DCID_dict"]
    
    # Dictionary to store instances of device connector
    deviceConnectors = {}

    # Creating device connectors according to their IDs and registration details of their plant units
    for DCID,plantConfig in DCID_dict.items():
        DC_name = f"raspbery_{DCID}"
        deviceConnectors["DC_name"] = Device_connector(catalog_url, plantConfig, baseClientID, DCID, broker, port)


    # Threding can be used for registeration not to delay for sensor data
    t = 0
    while t < 600:
        if t%100 == 0:
            for DC in deviceConnectors.values():
                DC.registerer()       
            
        for DC in deviceConnectors.values():
            DC.send_data()
        time.sleep(1)
        t+=1