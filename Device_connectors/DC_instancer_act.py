from device_connector_act import Device_connector_act
import json
import time
import cherrypy


if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    # Config files of actuating device connectors
    settingActFile = "setting_act.json"

    with open(settingActFile) as fp:
        settingAct = json.load(fp)
        
    baseClientID = settingAct["clientID"]

    ## DCID_act_dict -> device connectors' ID and corresponding plant configuration only containing devices list and last update
    # "01":{"devicesList": []} 
    DCID_act_dict = settingAct["DCID_dict"]
    
    # Dictionary to store instances of device connector
    deviceConnectorsAct = {}

    for DCID, plantConfig in DCID_act_dict.items():
        DC_name = f"arduino_{DCID}"
        deviceConnectorsAct[DC_name] = Device_connector_act(catalog_url, plantConfig, baseClientID, DCID)

    # Cherrypy configuration
    conf = {"/": {
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on':True
        }
    }
    cherrypy.config.update({'server.socket_port': 8086})

    # Threding can be used for registeration not to delay for sensor data
    try:
        t = 0
        while t < 600:
            if t%100 == 0:
                for DC_name, DC in deviceConnectorsAct.items():
                    DC.registerer()
                    time.sleep(1)

                    # Only once establishing the paths for every device connector
                    if t == 0:
                        cherrypy.tree.mount(DC,f'/{DC_name}',conf)
                    time.sleep(1)

                # Starting the server
                if t == 0:
                    cherrypy.engine.start()

            time.sleep(1)
            t+=1
    
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Shutting down...")
        for DC in deviceConnectorsAct.values():
            DC.stop()
        # Terminate the webservice    
        cherrypy.engine.block()
    
    finally:
        for DC in deviceConnectorsAct.values():
            # Stop MQTT client
            DC.stop()

        # Terminate the webservice    
        cherrypy.engine.block()