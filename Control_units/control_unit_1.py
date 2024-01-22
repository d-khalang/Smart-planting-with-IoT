from MyMQTT import MyMQTT
# function used form MyMQTT -> start, stop, myPublish, mySubscribe
import requests
import json
import time
import sched
from datetime import date, datetime
import copy


class Controler():
    def __init__(self, catalog_url):
        self.catalog_url = catalog_url
        self.clientID = "skyFarming_DS4SST"+ "_C"   # Controler
        self.topic = self.get_main_topic()+"/sensors/#"
        self.PERIODIC_UPDATE_INTERVAL = 600  # seconds
        
        # Schedule updating the plant lists and plant kinds every 10 minutes
        # Creating self.plants and self.plantKinds
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantList_update, ())
        self.scheduler.run(blocking=False)

        # Requesting to the catalog for broker's information
        try:
            broker, port = self.get_broker()
            
        except (TypeError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to get the broker's information. Probably server is down. Error:{e}")
            return

        self.client = MyMQTT(self.clientID, broker, port, self)
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

        # Finding out the levelID and plantID of the plant from which the data received 
        levelID, plantID = int(topic.split("/")[2]), int(topic.split("/")[3])
        senKind = event["n"].lower()

        # Classifing and analysing the data according to the type of transmiter sensor
        if senKind == "temperature":
            # Processing temperature data, generationg the command and sending to actuators
            self.send_temp_command(levelID, plantID, event["v"])

        elif senKind == "light":
            self.send_light_command(levelID, plantID, event["v"])
        
        elif senKind == "ph":
            self.send_PH_command(levelID, plantID, event["v"])
        
        elif senKind == "waterLevel":
            self.send_waterLevel_command(levelID, plantID, event["v"])
        
        elif senKind == "tds":
            self.send_TDS_command(levelID, plantID, event["v"])
   
    # Get the specific plant dictionary and its plant kind name
    def find_plant(self, levelID, plantID):
        for plant in self.plants:
            if plant["levelID"] == levelID and plant["plantID"] == plantID:
                thePlant = plant
                break

        plantKindName = thePlant["plantKind"]

        return thePlant, plantKindName



    # Processing the temperature data for each subtopic(correcponding level and plant unit)
    def send_temp_command(self, levelID, plantID, value):
        # No need to update every time as it is being updated each 10 min
        # Updating the plant info by a get request to the catalog
        # try:
        #     thePlant_req = requests.get(self.catalog_url+"plant/"+str(levelID)+"/"+str(plantID))
        
        # except requests.exceptions.RequestException as e:
        #     return f"Error during GET request for getting the plant: {e}"

        # Get the specific plant dictionary and its plant kind name
        plant, plantKindName = self.find_plant(levelID, plantID)
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
        msg = copy.deepcopy(self.msg)

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        
        # Check the temperature as regard to the plant suitable temperature
        if value < minTemp and heater_status == "OFF":
            print("Temperature less than threshold, Turn ON the heater")
            topic += "heater_switch"
            msg["e"][0]["v"] = "ON"

        elif value > maxTemp and fan_status == "OFF":
            print("Temperature more than threshold, Turn ON the fan")
            topic += "fan_switch"
            msg["e"][0]["v"] = "ON"
        
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
            print(f"{msg['e'][0]['v']} is published on topic: {topic}")
            
        
    # Processing the brightness data and send command if intervention is needed
    def send_light_command(self, levelID, plantID, value):
        # Getting the specific plant dictionary and its plant kind name
        plant, plantKindName = self.find_plant(levelID, plantID)

        # Getting the suitable light of the corresponding plant kind
        for plantKindDict in self.plantKinds:
            if plantKindDict["plantKind"] == plantKindName:
                vegetativeLightRange, floweringLightRang = plantKindDict["vegetativeLightRange"], plantKindDict["floweringLightRang"]

        # Status of the light switch actuators of the plant
        lightSwitch_status = None
        for device in plant["devicesList"]:
            if device["deviceName"] == "light_switch":
                lightSwitch_status = device["deviceStatus"]
        
        if not lightSwitch_status:
            print('failed to get the status of the light switch')

        plantingDate = plant["plantingDate"]
        plantAge = self.days_difference_from_today(plantingDate)

        # Structure the SenML message
        msg = copy.deepcopy(self.msg)

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        msgValue = None

        ## availableStatuses: ["OFF","LOW","MID","HIGH"]
        # Vegetative stage
        if plantAge <= 15:
            # If brightness is less that what is expected in vegetetive stage
            # Ligh switch will be put on one level stronger
            if value < vegetativeLightRange[0]:
                if lightSwitch_status == "OFF":
                    msgValue = "LOW"
                elif lightSwitch_status == "LOW":
                    msgValue = "MID"
                elif lightSwitch_status == "MID":
                    msgValue = "HIGH"

            # If brightness is in the range of flowering stage
            # Ligh switch will be put on one level weaker
            elif value in range(floweringLightRang[0], floweringLightRang[1]):
                if lightSwitch_status == "HIGH":
                    msgValue = "MID"
                elif lightSwitch_status == "MID":
                    msgValue = "LOW"
                elif lightSwitch_status == "LOW":
                    msgValue = "OFF"

            # If brightness is way more than what is expected 
            # Ligh switch will be shut down
            elif value > floweringLightRang[1]:
                if lightSwitch_status != "OFF":
                    msgValue = "OFF"
                

        # Flowering stage
        elif plantAge > 15:
            ## Set the switch to full power
            if value < vegetativeLightRange[0]:
                if lightSwitch_status != "HIGH":
                    msgValue = "HIGH"

            # One level forward
            elif value in range(vegetativeLightRange[0], vegetativeLightRange[1]):
                if lightSwitch_status == "OFF":
                    msgValue = "LOW"
                elif lightSwitch_status == "LOW":
                    msgValue = "MID"
                elif lightSwitch_status == "MID":
                    msgValue = "HIGH"

            # One level backward
            elif value > floweringLightRang[1]:
                if lightSwitch_status == "HIGH":
                    msgValue = "MID"
                elif lightSwitch_status == "MID":
                    msgValue = "LOW"
                elif lightSwitch_status == "LOW":
                    msgValue = "OFF"

        if msgValue:
            topic += "light_switch"
            msg["e"][0]["v"] = msgValue
            # Sending command to the actuators    
            self.client.myPublish(topic, msg)
            print(f"{msg['e'][0]['v']} is published on topic: {topic}")



    # Processing the PH data and send command if intervention is needed
    def send_PH_command(self, levelID, plantID, value):
        # Getting the specific plant dictionary and its plant kind name
        plant, plantKindName = self.find_plant(levelID, plantID)

        # Getting the suitable PH range of the corresponding plant kind
        for plantKindDict in self.plantKinds:
            if plantKindDict["plantKind"] == plantKindName:
                PHRange = plantKindDict["PHRange"]

        # Status of the light switch actuators of the plant
        PHActuator_status = None
        for device in plant["devicesList"]:
            if device["deviceName"] == "PH_actuator":
                PHActuator_status = device["deviceStatus"]
        
        if not PHActuator_status:
            print('failed to get the status of the PH actuator')

        plantingDate = plant["plantingDate"]

        # Structure the SenML message
        msg = copy.deepcopy(self.msg)

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        msgValue = None

        # Setting the command
        if value < PHRange[0]:
            msgValue = "release_PH_high"
        elif value > PHRange[1]:
            msgValue = "release_PH_low"

        if msgValue:
            topic += "PH_actuator"
            msg["e"][0]["v"] = msgValue
            # Sending command to the actuators    
            self.client.myPublish(topic, msg)
            print(f"{msg['e'][0]['v']} is published on topic: {topic}")

        

    # Processing the water level data and send command if intervention is needed
    def send_waterLevel_command(self, levelID, plantID, value):
        # Getting the specific plant dictionary and its plant kind name
        plant, plantKindName = self.find_plant(levelID, plantID)

        # Getting the suitable PH range of the corresponding plant kind
        for plantKindDict in self.plantKinds:
            if plantKindDict["plantKind"] == plantKindName:
                minWater = plantKindDict["minWaterLevel"]

        # Status of the light switch actuators of the plant
        waterPump_status = None
        for device in plant["devicesList"]:
            if device["deviceName"] == "water_pump":
                waterPump_status = device["deviceStatus"]
        
        if not waterPump_status:
            print('failed to get the status of the water pump')

        # Structure the SenML message
        msg = copy.deepcopy(self.msg)

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        msgValue = None

        # Setting the command
        if value < minWater:
            msgValue = "pour_water"

        if msgValue:
            topic += "water_pump"
            msg["e"][0]["v"] = msgValue
            # Sending command to the actuators    
            self.client.myPublish(topic, msg)
            print(f"{msg['e'][0]['v']} is published on topic: {topic}")




    # Processing the TDS data and send command if intervention is needed
    def send_TDS_command(self, levelID, plantID, value):
        # Getting the specific plant dictionary and its plant kind name
        plant, plantKindName = self.find_plant(levelID, plantID)

        # Getting the suitable light of the corresponding plant kind
        for plantKindDict in self.plantKinds:
            if plantKindDict["plantKind"] == plantKindName:
                seedingTDSRange , vegetativeTDSRange, floweringTDSRang = plantKindDict["seedingTDSRange"], plantKindDict["vegetativeTDSRange"], plantKindDict["floweringTDSRang"]

        # Status of the light switch actuators of the plant
        TDSActuator_status = None
        for device in plant["devicesList"]:
            if device["deviceName"] == "TDS_actuator":
                TDSActuator_status = device["deviceStatus"]
        
        if not TDSActuator_status:
            print('failed to get the status of the light switch')

        plantingDate = plant["plantingDate"]
        plantAge = self.days_difference_from_today(plantingDate)

        # Structure the SenML message
        msg = copy.deepcopy(self.msg)

        # Assigning the same level and plant ID as the message received to the base name (also the topic)
        msg["bn"] += f"{levelID}/{plantID}/"
        topic = msg["bn"]
        msg["e"][0]["t"] = str(time.time())
        msgValue = None

        ## The actuator can only 'release solution' which we assume increase the TDS around 100 ppm
        # seeding stage
        if plantAge <= 5:
            # If TDs is less that what is expected in seeding stage
            if value < seedingTDSRange[0]:
                msgValue = "release_solution"

        # Vegetative stage
        elif plantAge > 5 and plantAge <= 15:
            if value < floweringTDSRang[0]:
                msgValue = "release_solution"

        # Flowering stage
        elif plantAge > 15:
            if value < vegetativeTDSRange[0]:
                msgValue = "release_solution"


        if msgValue:
            topic += "TDS_actuator"
            msg["e"][0]["v"] = msgValue
            # Sending command to the actuators    
            self.client.myPublish(topic, msg)
            print(f"{msg['e'][0]['v']} is published on topic: {topic}")



    # Calculating the age of the plant (how many days in the past it was planted)
    def days_difference_from_today(self, plantingDate):
        today = date.today()

        # Convert the format from string to date obj
        theDate = datetime.strptime(plantingDate, "%Y-%m-%d").date()

        # Calculate the difference in days
        difference = (today - theDate).days

        return difference


    # Subscribe to the main topic
    def get_main_topic(self):
        rq = requests.get(self.catalog_url+"topic")
        topic = rq.text.strip('"')
        return topic
    
    # Requesting to the catalog for broker's information
    def get_broker(self):
        try:
            req_b = requests.get(self.catalog_url+"broker")
            broker, port = req_b.json()["IP"], int(req_b.json()["port"])
            print("Broker's info received\n")
            return broker, port
        
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request for the broker: {e}\n\n")

    
    
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

    controler = Controler(catalog_url)
    for i in range(60):
            time.sleep(1)
    controler.exit()