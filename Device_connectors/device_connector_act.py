from MyMQTT import MyMQTT
import requests
import time
import json
import copy
import cherrypy



class Device_connector_act():
    exposed = True
    def __init__(self, catalog_url, plantConfig, baseClientID,DCID):
        self.catalog_url, self.plantConfig = catalog_url, plantConfig
        self.clientID = baseClientID+DCID+"_DCA"    # Device connector actuator
        self.devices = self.plantConfig['devicesList']

        # Requesting to the catalog for broker's information
        try:
            broker, port = self.get_broker()
            
        except (TypeError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to get the broker's information. Probably server is down. Error:{e}")
            return
        
        self.client = MyMQTT(self.clientID, broker, port, self)
        self.client.start()
        
        levelID, plantID = DCID[0], DCID[1]
        self.topic = f"skyFarming/commands/{levelID}/{plantID}/#"
        self.client.mySubscribe(self.topic)


    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) != 0:
            if uri[0] == "devices":
                #devices = json.dumps(self.devices)
                return self.devices
            else:
                return "Wrong URL, Go to devices to see the devices list"
            
        return "Go to devices to see the devices list"

        
    # Will be triggered when a message is received
    def notify(self, topic, payload):
        msg = json.loads(payload)

        # Part of the message related to the event happened
        event = msg["e"][0]
        print(f"{topic} measured a {event['n']} of {event['v']} {event['u']} at time {event['t']}")

        senKind = topic.strip().split('/')[-1]
        print(f"{senKind} -> {event['v']}")

        ####
        #### changing the staus of the device on the catalog
        if senKind.lower() in ["fan_switch", "heater_switch", "light_switch"]:
            for device in self.devices:
                if senKind.lower() == device["deviceName"].lower():
                    print(senKind)
                    device.update({"deviceStatus": event['v']})

        # if senKind == "fan_switch":
        #     pass
        # elif senKind == "heater_switch":
        #     pass        

    ## Unsubscribing and disconnecting from the broker
    def stop(self):
        self.client.stop()

    # Requesting to the catalog for broker's information
    def get_broker(self):
        try:
            req_b = requests.get(self.catalog_url+"broker")
            broker, port = req_b.json()["IP"], int(req_b.json()["port"])
            print("Broker's info received\n")
            return broker, port
        
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request for the broker: {e}\n\n")


    # Registering the devices of the plant  
    def registerer(self):
        # Add all devices of by one
        for device in self.devices:
            try:
                postReq = requests.post(self.catalog_url+"devices", json = device)
            except requests.exceptions.RequestException as e:
                return f"Error during POST request of adding device: {e}"
            
            try:
                postReq_status = int(postReq.text.split(",")[1].strip(" ]"))
            except ValueError as e:
                return f"Unsuccessful POST request of adding device, Unknown response{e}"
        
            # Check if post request was successful
            if postReq_status == 201:
                return "POST request successful"
        
            # If the device exists, checks for the put request
            elif postReq_status == 202:
                try:
                    putReq = requests.put(self.catalog_url+"devices", json = device)
                    putReq_status = int(putReq.text.split(",")[1].strip(" ]"))
                except requests.exceptions.RequestException as e:
                    return f"Error during PUT request of updating the device: {e}"
                except ValueError as e:
                    return f"Unsuccessful PUT request of updating the device, Unknown response{e}"

                if putReq_status == 201:
                    print("device registeration is updated successfully")
                    return "PUT request successful"
                else:
                    return f"""POST: {postReq.text}
                    PUT: {putReq.text}"""
            else:
                return f"Unkown response: {postReq_status}"
            




