from MyMQTT2 import MyMQTT
import requests
import sched
import time
import json


class Adopter():
    def __init__(self, catalog_url, channel_API, levelID, plantID):
        self.CLIENT_ID = "skyFarming_DS4SST_THA" # Constant + Think speak adopter
        self.catalog_url = catalog_url
        self.channel_API = channel_API  # API for writing on thinkspeak
        self.levelID, self.plantID = levelID, plantID
        
        # Setting all the needed topics to None
        self.tempTopic, self.PHTopic, self.lightTopic = None, None, None

        # The interval for updating the topics
        self.PERIODIC_UPDATE_INTERVAL = 600 # seconds

        # Requesting to the catalog for broker's information
        try:
            broker, port = self.get_broker()
            
        except (TypeError, ValueError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to get the broker's information. Probably server is down. Error:{e}")
            return
        
        # Creating MQTT subscriber
        self.client = MyMQTT(self.CLIENT_ID, broker, port, self)

        # Schedule updating the topics for the sensors of the plant every 10 minutes
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_topics_update, ())
        self.scheduler.run(blocking=False)




    # Triggered when a message recieved
    def notify(self, topic, payload):
        msg = json.loads(payload)
        event = msg["e"][0]
        print(f"{topic} measured a {event['n']} of {event['v']} {event['u']} at time {event['t']}")

        senKind = topic.split("/")[-1].strip().lower()

        # Checking the kind of sensor from which the data is received 
        # Field 1 for temperature ,Field 2 for PH, Field 3 for light
        if senKind == "temperature":
            channedlField = "1"
            
        elif senKind == "ph":
            channedlField = "2"
            
        elif senKind == "light":
            channedlField = "3"
        
        try:
            requests.get(self.channel_API+f"{channedlField}={str(event['v'])}")     
            print(f"{senKind} is writen on thinkspeak successfully\n")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during writing {senKind} on thinkspeak channel: {e}")


    # Connect to the broker and subscribe to all the interesting topics
    def allStart(self):
        self.client.start()
        if self.tempTopic:
            self.client.mySubscribe(self.tempTopic)
        if self.PHTopic:
            self.client.mySubscribe(self.PHTopic)
        if self.lightTopic:
            self.client.mySubscribe(self.lightTopic)
        
    
    # MyMQTT2 stop, takes care of unsubscribing all the topics
    def allStop(self):
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
        



    def periodic_topics_update(self):
        # Getting the plant info by a GET request to the catalog
        try:
            thePlant_req = requests.get(self.catalog_url+"plant/"+str(self.levelID)+"/"+str(self.plantID))
        
        except requests.exceptions.RequestException as e:
            return f"Error during GET request for getting the plant: {e}"
        
        plant = thePlant_req.json()
        
        # Updating the topics
        tempTopicUpdate, PHTopicUpdate, lightTopicUpdate = False, False, False

        tempTopicUpdate, self.tempTopic = self.update_topic_for_measure_type(plant["devicesList"], "temperature")
        PHTopicUpdate, self.PHTopic = self.update_topic_for_measure_type(plant["devicesList"], "PH")
        lightTopicUpdate, self.lightTopic = self.update_topic_for_measure_type(plant["devicesList"], "light")

                            

        # Check if the topics are retrived successfully
        # If not remove the corresponding topic to avoid subscription
        if not tempTopicUpdate:
            self.tempTopic = None
            print("Failed to update the temperature topic")

        if not PHTopicUpdate:
            self.PHTopic = None
            print("Failed to update the PH topic")

        if not lightTopicUpdate:
            self.lightTopic = None
            print("Failed to update the light topic")

        
        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_topics_update, ())


    # Going through the devices of the plant
        # checking the measureType and if its among the meant ones, it get's the topic
    def update_topic_for_measure_type(self, devicesList, measureType):
        topicUpdate, topic = False, None

        for device in devicesList:
            if measureType in device["measureType"]:
                for service_detail in device["servicesDetails"]:
                    for t in service_detail["topic"]:
                        if t.split("/")[-1].lower() == measureType.lower():
                            topic = t
                            topicUpdate = True
                            break

            # Avoid iteration over all devices
            if topicUpdate:
                break

        return topicUpdate, topic


if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    API_key = "SG9EQF4I37UYYFHY"
    channel_API = f"https://api.thingspeak.com/update?api_key={API_key}&field"
    levelID = 0
    plantID = 1

    adopter = Adopter(catalog_url, channel_API, levelID, plantID)

    adopter.allStart()
    for i in range(120):
        time.sleep(1)
    adopter.allStop()