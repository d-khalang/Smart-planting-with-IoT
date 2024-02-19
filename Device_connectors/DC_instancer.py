from device_connector import Device_connector
import json
import time
import cherrypy

if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    # plantConfigFileName = "devices_configuration.json"
    settingFile = "setting_sen.json"
    
    
    # Information needed for creating an Mqtt client
    with open(settingFile) as fp:
        setting = json.load(fp)
        
    ## DCID_dict -> device connectors' ID and corresponding plant configuration 
    baseClientID, DCID_dict = setting["clientID"], setting["DCID_dict"]
    
    # Dictionary to store instances of device connector
    deviceConnectors = {}

    # Creating device connectors according to their IDs and registration details of their plant units
    for DCID,plantConfig in DCID_dict.items():
        DC_name = f"raspberry_{DCID}"
        deviceConnectors[DC_name] = Device_connector(catalog_url, plantConfig, baseClientID, DCID)

    # Cherrypy configuration
    conf = {"/": {
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on':True
        }
    }
    cherrypy.config.update({'server.socket_port': 8085})

    # Threding can be used for registeration not to delay for sensor data
    try:
        t = 0
        while t < 600:
            if t%100 == 0:
                for DC_name, DC in deviceConnectors.items():
                    DC.registerer()

                    # Only once establishing the paths for every device connector
                    if t == 0:
                        cherrypy.tree.mount(DC,f'/{DC_name}',conf)
                    time.sleep(2)       
                
                # Starting the server
                if t == 0:
                    cherrypy.engine.start()

            # Sending data almost every one min + time of the delay
            # For getting the avg of data        
            for DC in deviceConnectors.values():
                DC.send_data()

            time.sleep(1)
            t+=1

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Shutting down...")
        # Terminate the webservice    
        cherrypy.engine.block()
        
    finally:
        # Terminate the webservice    
        cherrypy.engine.block()