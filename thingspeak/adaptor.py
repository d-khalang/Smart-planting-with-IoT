import requests
import sched
import time
import json
from MyMQTT2 import MyMQTT
import cherrypy

class Adaptor_webservice():
    exposed = True
    def __init__(self):
        pass
    
    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) != 0:
            if uri[0] == "channels_detail":
                channelsDetail = adaptor.get_channel_detail()
                return channelsDetail
            else:
                return "Go to /channels_detail"
        else:
                return "Go to /channels_detail"
        

class Adaptor():
    def __init__(self, catalog_url, channel_API, user_API_key, clientID):
        self.PERIODIC_UPDATE_INTERVAL = 600  # Seconds
        self.catalog_url = catalog_url
        self.channel_API = channel_API
        self.user_API_key = user_API_key
        self.clientID = clientID
        self.plants = None
        self.channelsDetail = None
        self.availableMeasureTypes = ["temperature", "PH", "light", "TDS", "waterLevel"]

        # Requesting to the catalog for broker's information
        broker, port = self.get_broker()
            
        # Creating MQTT subscriber
        self.client = MyMQTT(self.clientID, broker, port, self)
    
        # Schedule updating the plant lists and plant kinds every 10 minutes
        # Creating self.plants and self.plantKinds
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantList_update, ())
        self.scheduler.run(blocking=False)

        self.check_and_create_channel()


    # To get the channels and fields information for user interface
    def get_channel_detail(self):
        return self.channelsDetail

    # Triggered when a message recieved
    def notify(self, topic, payload):
        msg = json.loads(payload)
        event = msg["e"][0]
        print(f"{topic} measured a {event['n']} of {event['v']} {event['u']} at time {event['t']}")

        # Identifing the level, plant, and kind of sensor from which the data is received 
        # skyFarming/sensors/{levelID}/{plantID}
        seperatedTopic = topic.strip().split("/")
        levelIDstr, plantIDstr, senKind = seperatedTopic[2], seperatedTopic[3], seperatedTopic[4]

        field_available = False
        for channelName, channelDetail in self.channelsDetail.items():
            if channelName == levelIDstr+plantIDstr:
                channel_API = channelDetail["writeApiKey"]
                for field, senName in channelDetail["fields"].items():
                    if senName == senKind:
                        channedlField = field
                        field_available = True
                        break
                    

        
        # Writing on Thingspeak channel
        if field_available:
            try:
                response = requests.get(self.channel_API+f"api_key={channel_API}&{channedlField}={str(event['v'])}")     
                print(f"{senKind} on channel {channelName} and {field} is writen on thinkspeak with code {response.text}\n")
            
            except (requests.exceptions.RequestException, UnboundLocalError) as e:
                print(f"Error during writing {senKind} on thinkspeak channel: {e}")





    def check_and_create_channel(self):
        self.channelsDetail = {}
        # Step 1: Send request to retrieve list of channels
        url = f"https://api.thingspeak.com/channels.json?api_key={self.user_API_key}"
        response = requests.get(url)
        channels = response.json()

        for plant in self.plants:
            levelID, plantID = plant["levelID"], plant["plantID"]
            channelName = str(levelID)+str(plantID)

            # Dictionary mapping field numbers to their names according to data sensing devices
            fieldNamesDict = {}
            fieldNum = 1
            for device in plant["devicesList"]:
                for measureType in device["measureType"]:
                    if measureType in self.availableMeasureTypes:
                        fieldNamesDict[f"field{fieldNum}"] = measureType
                    fieldNum += 1
                    

            # Adding the information of channels' fields to the channel detail dict
            self.channelsDetail[channelName] = {"fields" : fieldNamesDict}

            # Step 2: Check if the channel exists
            channel_exists = any(channel['name'] == channelName for channel in channels)

            if channel_exists:
                print(f"Channel '{channelName}' already exists.")
                channelId, writeApiKey = next((channel['id'], channel["api_keys"][0]["api_key"]) for channel in channels if channel['name'] == channelName)
                self.channelsDetail[channelName]["writeApiKey"] = writeApiKey
                self.channelsDetail[channelName]["channelId"] = channelId

            else:
                # Step 3: Create the channel
                create_channel_url = "https://api.thingspeak.com/channels.json"
                create_channel_payload = {"api_key": self.user_API_key, "name": channelName, "public_flag":"true"}

                # Creating the fields of the channel
                for fieldID, fieldName in fieldNamesDict.items():
                    create_channel_payload[fieldID] = fieldName

                # ADD TRY AND except
                try:
                    create_channel_response = requests.post(create_channel_url, params=create_channel_payload)
                    created_channel = create_channel_response.json()
                    channelID, writeApiKey = created_channel['id'], created_channel["api_keys"][0]["api_key"]
                    print(f"Channel '{channelName}' created with ID {channelId}")
                    self.channelsDetail[channelName]["writeApiKey"] = writeApiKey
                    self.channelsDetail[channelName]["channelId"] = channelId
                except requests.exceptions.RequestException as e:
                    print(f"Failed to create channel {channelName} because: {e}")



    
    # Connect to the broker and subscribe once for each operating plant
    def allStart(self):
        self.client.start()
        for channelName in self.channelsDetail.keys():
            levelID, plantID = channelName[0], channelName[1]

            self.client.mySubscribe(f"skyFarming/sensors/{levelID}/{plantID}/#")

        
    
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


    # Keeping only the active plant units (with the devices)
    def update_plantList(self, plants):
        newPlantList = []
        for plant in plants:
            if plant["devicesList"] != []:
                newPlantList.append(plant)

        self.plants = newPlantList

    # Updating the plant lists every 10 minutes
    def periodic_plantList_update(self):
        # Requesting to the catalog
        try:
            req_p = requests.get(self.catalog_url+"plants")
            print("Plant list is updated(adaptor)\n")
        
        except requests.exceptions.RequestException as e:
            return f"Error during GET request: {e}"
         
        plants = req_p.json()
        self.update_plantList(plants)

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_plantList_update, ())


if __name__ == "__main__":
    conf = {"/": {
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on':True
        }
    }
    catalog_url = "http://127.0.0.1:8080/"
    channel_API = "https://api.thingspeak.com/update?"  #api_key={API_key}&field"
    user_API_key = "CLZB835RLN16Q1LK"
    clientId = "skyFarming_DS4SST_THA" # Constant + Think speak adopter
    adaptor = Adaptor(catalog_url, channel_API, user_API_key, clientId)
    adaptor.allStart()

    cherrypy.config.update({'server.socket_port': 8099})
    webService = Adaptor_webservice()
    cherrypy.tree.mount(webService,'/',conf)
    cherrypy.engine.start()

    try:
        # Wait for 240 seconds
        for _ in range(240):
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Shutting down...")
        adaptor.allStop()
        cherrypy.engine.stop()
    finally:
        cherrypy.engine.block()