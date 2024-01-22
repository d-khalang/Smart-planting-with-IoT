from MyMQTT import MyMQTT
from sensors import TempSen, LightSen, PHSen, WaterLevelSen, TDSSen
import requests
import time
import json
import copy

### Defining a general sensor publisher
class senPublisher():
    def __init__(self, clientID, broker, port):
        self.client = MyMQTT(clientID, broker, port, None)
        self.start()  

    ## Connecting to the broker
    def start(self):
        self.client.start()

    ## Disconnecting from the broker
    def stop(self):
        self.client.stop()

    def publish(self, topic, msg):
        self.client.myPublish(topic, msg)
        



class Device_connector():
    def __init__(self, catalog_url, plantConfig, baseClientID,DCID):
        self.catalog_url, self.plantConfig = catalog_url, plantConfig
        clientID = baseClientID+DCID+"_DCS"    # Device connector sensor

        # Requesting to the catalog for broker's information
        try:
            broker, port = self.get_broker()
            
        except (TypeError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to get the broker's information. Probably server is down. Error:{e}")
            return
        
        self.senPublisher = senPublisher(clientID, broker, port)
        self.DATA_SENDING_INTERVAL = 10    # each x seconds get the avg of each second data and send

        levelID, plantID = DCID[0], DCID[1]
        self.msg = {
            "bn": f"skyFarming/sensors/{levelID}/{plantID}/",
            "e": [
                {
                    "n": 'senKind',
                    "u": 'unit',
                    "t": None,
                    "v": None
                }
            ]
        }

        ## Creating sensor objects
        self.tempSen = TempSen()
        self.lightSen = LightSen()
        self.PHSen = PHSen()
        self.waterLevelSen = WaterLevelSen()
        self.TDSSen = TDSSen()

    # Getting data from 'get_sen_data' and sending it to message broker
    def send_data(self):
        # Get the average data
        msgTemp, msgLight, msgPH, msgWaterLevel, msgTDS = self.get_sen_data()

        # Connect the publisher, publish the message and disconnect
        self.senPublisher.start()
        print("\npublisher started")
        time.sleep(1)

        self.senPublisher.publish(msgTemp["bn"], msgTemp)
        print(f"message {msgTemp['e'][0]['v']} published on topic: {msgTemp['bn']}")
        time.sleep(1)
        self.senPublisher.publish(msgLight["bn"], msgLight)
        print(f"message {msgLight['e'][0]['v']} published on topic: {msgLight['bn']}")
        time.sleep(1)
        self.senPublisher.publish(msgPH["bn"], msgPH)
        print(f"message {msgPH['e'][0]['v']} published on topic: {msgPH['bn']}")
        time.sleep(1)
        self.senPublisher.publish(msgWaterLevel["bn"], msgWaterLevel)
        print(f"message {msgWaterLevel['e'][0]['v']} published on topic: {msgWaterLevel['bn']}")
        time.sleep(1)
        self.senPublisher.publish(msgTDS["bn"], msgTDS)
        print(f"message {msgTDS['e'][0]['v']} published on topic: {msgTDS['bn']}")

        time.sleep(1)
        self.senPublisher.stop()
        print("publisher stoped")



        # for now just tempreture sensor, input like  self.tempSen 
    def get_sen_data(self):
        tempData, lightData, PHData, waterLevelData, TDSData = [], [], [], [], []

        # Generate a value every second for every sensor
        for i in range(self.DATA_SENDING_INTERVAL):
            datum = self.tempSen.generate_data()
            tempData.append(datum)

            datum = self.lightSen.generate_data()
            lightData.append(datum)

            datum = self.PHSen.generate_data()
            PHData.append(datum)

            datum = self.waterLevelSen.generate_data()
            waterLevelData.append(datum)

            datum = self.TDSSen.generate_data()
            TDSData.append(datum)
            time.sleep(1)
        
        # !!! create a function to get average and change the message
            # there must be a data dict having the keys temp, light, ....
        # Get the mean each 10 second
        avgTemp = round(sum(tempData)/len(tempData), 1)
        avgLight = round(sum(lightData)/len(lightData), 1)
        avgPH = round(sum(PHData)/len(PHData), 2)
        avgWaterLevel = round(sum(waterLevelData)/len(waterLevelData), 2)
        avgTDS = round(sum(TDSData)/len(TDSData), 1)

        # Updating the message
        msgTemp, msgLight, msgPH, msgWaterLevel, msgTDS = copy.deepcopy(self.msg), copy.deepcopy(self.msg), copy.deepcopy(self.msg), copy.deepcopy(self.msg), copy.deepcopy(self.msg),
        
        msgTemp['e'][0].update({"n":"temperature", "u":"Cel", "t":str(time.time()), "v":avgTemp})
        msgTemp["bn"] += "temperature"

        msgLight['e'][0].update({"n":"light", "u":"μmol/m²/s", "t":str(time.time()), "v":avgLight})
        msgLight["bn"] += "light"

        msgPH['e'][0].update({"n":"PH", "u":"range", "t":str(time.time()), "v":avgPH})
        msgPH["bn"] += "PH"

        msgWaterLevel['e'][0].update({"n":"waterLevel", "u":"m", "t":str(time.time()), "v":avgWaterLevel})
        msgWaterLevel["bn"] += "waterLevel"

        msgTDS['e'][0].update({"n":"TDS", "u":"bpm", "t":str(time.time()), "v":avgTDS})
        msgTDS["bn"] += "TDS"

        return msgTemp, msgLight, msgPH, msgWaterLevel, msgTDS


    # Requesting to the catalog for broker's information
    def get_broker(self):
        try:
            req_b = requests.get(self.catalog_url+"broker")
            broker, port = req_b.json()["IP"], int(req_b.json()["port"])
            print("Broker's info received\n")
            return broker, port
        
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request for the broker: {e}\n\n")


    # Registering the plant and its devices  
    def registerer(self):
        # Add the plant
        try:
            postReq = requests.post(self.catalog_url+"plants", json = self.plantConfig)
        except requests.exceptions.RequestException as e:
            return f"Error during POST request: {e}"
        
        try:
            postReq_status = int(postReq.text.split(",")[1].strip(" ]"))
        except ValueError as e:
            return f"Unsuccessful POST request, Unknown response{e}"
        
        # Check if post request was successful
        if postReq_status == 201:
            return "POST request successful"
        
        # If the plant excists, checks for the put request
        elif postReq_status == 202:
            try:
                putReq = requests.put(self.catalog_url+"plants", json = self.plantConfig)
                putReq_status = int(putReq.text.split(",")[1].strip(" ]"))
            except requests.exceptions.RequestException as e:
                return f"Error during PUT request: {e}"
            except ValueError as e:
                return f"Unsuccessful PUT request, Unknown response{e}"

            if putReq_status == 201:
                print("Plant registeration is updated successfully")
                return "PUT request successful"
            else:
                return f"""POST: {postReq.text}
                PUT: {putReq.text}"""
        else:
            return f"Unkown response: {postReq_status}"
            




