from MyMQTT import MyMQTT
# function used form MyMQTT -> start, stop, myPublish, mySubscribe
import requests
import json
import time
import sched


class Controler():
    def __init__(self, catalog_url, clientID, broker, port):
        self.catalog_url = catalog_url
        self.topic = self.get_main_topic()+"/sensors/#"
        self.PERIODIC_UPDATE_INTERVAL = 600  # seconds
        
        # Schedule updating the plant lists and plant kinds every 10 minutes
        # Creating self.plants and self.plantKinds
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantList_update, ())
        self.scheduler.run(blocking=False)


        ## Creating and stablishing MQTT client
        clientID += "_C"   # Controler
        self.client = MyMQTT(clientID, broker, port, self)
        # Connecting to the broker as both publisher and subscriber
        self.client.start()
        # Subscribe to the topic
        self.client.mySubscribe(self.topic)

        # The command message
        self.msg = {
            "bn": "skyFarming/commands/",
            "e": [
                {
                    "n": 'controler',
                    "u": 'command',
                    "t": None,
                    "v": None
                }
            ]
        }
        


    # Will be triggered when a message is received
    def notify(self, topic, payload):
        msg = json.loads(payload)

        # Part of the message related to the event happened
        event = msg["e"][0]
        print(f"{topic} measured a {event['n']} of {event['v']} {event['u']} at time {event['t']}")

        # Fanding out the levelID and plantID of the plant from which the data received 
        levelID, plantID = int(topic.split("/")[2]), int(topic.split("/")[3])
        senKind = event["n"].lower()

        # Classifing and analysing the data according to the type of transmiter sensor
        if senKind == "temperature":
            # Processing the data, generationg the command and sending to actuators
            self.send_command(levelID, plantID, event["v"])
   




    # Processing the data for each subtopic(correcponding level and plant unit)
    def send_command(self, levelID, plantID, value):
        
        # Updating the plant info by a get request to the catalog
        try:
            thePlant_req = requests.get(self.catalog_url+"plant/"+str(levelID)+"/"+str(plantID))
        
        except requests.exceptions.RequestException as e:
            return f"Error during GET request for getting the plant: {e}"
        
        plant = thePlant_req.json()
        plantKindName = plant["plantKind"]

        # other way: stororing and updating all the plants each time
        # plantFound = False
        # for plant in self.plants:
        #     if plant["levelID"] == levelID and plant["plantID"] == plantID:
        #         plantKindName = plant["plantKind"]
        #         plantFound = True
        #         break
        # if not plantFound:
        #     print(f"Plant not present. levelID: {levelID}, plantID: {plantID}")
        #     return
        
        # Getting the suitable temperature of the corresponding plant kind
        for plantKindDict in self.plantKinds:
            if plantKindDict["plantKind"] == plantKindName:
                minTemp, maxTemp, bestTempRange = plantKindDict["coldestTemperature"], plantKindDict["hottestTemperature"], plantKindDict["bestTemperatureRange"]
        
    
        # Status of the temp actuators of the plant     
        fan_status, heater_status = None, None
        for device in plant["devicesList"]:
            if device["deviceName"] == "fan_switch":
                fan_status = device["deviceStatus"]
            
            elif device["deviceName"] == "heater_switch":
                heater_status = device["deviceStatus"]

        if not (fan_status and heater_status):
            print('failed to get the status of the fan and heater')
        
        # Structure the SenML message
        msg = self.msg.copy()

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        
        # Check the temperature as regard to the plant suitable temperature
        if value < minTemp and heater_status == "OFF":
            print("Temperature less than threshold, Turn ON the heater")
            topic += "heater_switch"
            msg["e"][0]["v"] = "heater on"

        elif value > maxTemp and fan_status == "OFF":
            print("Temperature more than threshold, Turn ON the fan")
            topic += "fan_switch"
            msg["e"][0]["v"] = "cooler on"
        
        elif value in range(bestTempRange[0], bestTempRange[1]):
            if heater_status == "ON":
                topic += "heater_switch"
                msg["e"][0]["v"] = "OFF"
            if fan_status == "ON":
                topic += "fan_switch"
                msg["e"][0]["v"] = "OFF"

        # Returning the message carring on the order
        if msg["e"][0]["v"]:
            # Sending command to the actuators    
            self.client.myPublish(topic, msg)
            

  


    # subscribe to the main topic
    def get_main_topic(self):
        rq = requests.get(self.catalog_url+"topic")
        topic = rq.text.strip('"')
        return topic
    
    
        # self.plant is not needed in current stage
    # Updating the plant lists and plant kinds every 10 minutes
    def periodic_plantList_update(self):
        # Requesting to the catalog
        try:
            req_p = requests.get(self.catalog_url+"plants")
            req_pk = requests.get(self.catalog_url+"plantkinds")
            print("Plant and plant kind lists are updated\n")
        
        except requests.exceptions.RequestException as e:
            return f"Error during GET request: {e}"
         
        self.plants, self.plantKinds = req_p.json(), req_pk.json()

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_plantList_update, ())


    ## Disconnecting from the broker
    def exit(self):
        self.client.stop()




if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"

    with open("setting.json") as fp:
            setting = json.load(fp)
    clientID, broker, port = setting["clientID"], setting["broker"], setting["port"]

    controler = Controler(catalog_url, clientID, broker, port)
    for i in range(60):
            time.sleep(1)
    controler.exit()