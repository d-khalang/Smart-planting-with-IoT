import requests
import cherrypy
import sched
import time


class Operator_control():
    exposed = True
    def __init__(self, catalog_url, adaptor_url):
        self.catalog_url = catalog_url
        self.adaptor_url = adaptor_url
        self.PERIODIC_UPDATE_INTERVAL = 600  # Seconds
        self.plants = None
        self.realTimePlants = {}
        self.baseUrlActuators = None
        # Must get the channelDetail for the use of interface
        self.channelsDetail = None

    
        # Schedule updating the plant lists every self.PERIODIC_UPDATE_INTERVAL seconds
        # Creating self.plants
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantList_update, ())
        self.scheduler.run(blocking=False)


    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) != 0:
            if uri[0] == "plants":
                self.get_realtime_plant()
                return self.realTimePlants
            
            elif uri[0] == "channels_detail":
                if len(uri) > 1:
                    return self.get_channel_detail(uri[1])
                else: 
                    return "Enter name of the channel"
            else:
                return """Wrong URL, Go to '/plants' to see the real-time information of the operating plants. 
            Or go to '/channels_detail to see thingspeak's channels' information"""
            
        else:
            return """Go to '/plants' to see the real-time information of the operating plants. 
            Or go to '/channels_detail to see thingspeak's channels' information"""
        
        
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        if len(uri) != 0:
            # for recieving the messages for changing the status of the devices
            if uri[0] == "device_status":
                body = cherrypy.request.json
                deviceID = body["deviceID"]
                levelID = body["levelID"]
                plantID = body["plantID"]
                status = body["status"]
                deviceBodyMessage = {"deviceID": deviceID, "status": status}
                
                # Put request to the corresponding device connector to change the device status
                try:
                    req_pu = requests.put(self.baseUrlActuators+"/"+"arduino_"+levelID+plantID+"/device_status", json=deviceBodyMessage)
                    print("Post request response form the operator control", req_pu.text)

                except requests.exceptions.RequestException as e:
                    print(f"failed to put the device status on operator control. Error:{e}")

                return {"successfull":[deviceID, levelID, plantID, status]}
        else: return {"unsuccessfull":"No uri"}


    # Getting the detail of channels from thigspeak adaptor
    def get_channel_detail(self, channel_name):
        try:
            req_p = requests.get(self.adaptor_url + "channels_detail")
            print("Thingspeak channel detail is updated (interface)\n")
            channels_detail = req_p.json()
            # return channels_detail.get(channel_name)
            return channels_detail.get(channel_name)
        
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
            return None


    # Used in get_realtime_plant
    def request_device_connectors(self, urlSensors, urlActuators):
        # Request sensors device connector getting the info of plant and sensors
        try:
            req_p = requests.get(urlSensors)
            print("Sensors' list is updated (operator control)\n")
            plant = req_p.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request of getting sensors: {e}")
        
        # Request actuator device connector getting the actuators and adding them to the plant
        try:
            req_p = requests.get(urlActuators)
            print("actuators' list is updated (operator control)\n")
            actuatorsList = req_p.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request of getting the actuators: {e}")

        # Appending actuators to the plant devices list
        try:
            plant["devicesList"].extend(actuatorsList)
            return plant
        except (UnboundLocalError, TypeError) as e:
            print("Probablly faild to access the plant. Error:%s", e)
    

    # Used when user send a get request for plants
    def get_realtime_plant(self):
        for plant in self.plants:
            plantName = str(plant["levelID"])+str(plant["plantID"])

            # urlSensors contains the info of the plant and sensor devices
            # urlActuators contains only the actuator devices
            urlSensors, urlActuators = plant["urlSensors"], plant["urlActuators"]
            # For requesting the device connectors to change the status of the actuators 
            self.realTimePlants[plantName] = self.request_device_connectors(urlSensors, urlActuators)

    # Getting base actuator url for posting the devices' status
    def get_actuator_url(self):
        self.baseUrlActuators = "/".join(self.plants[0]["urlActuators"].strip().split('/')[0:3])
        

            


    # Updating the plant lists every self.PERIODIC_UPDATE_INTERVAL minutes
    def periodic_plantList_update(self):
        # Requesting to the catalog
        try:
            req_p = requests.get(self.catalog_url + "plants")
            print("Plant list is updated (operator control)\n")
            plants = req_p.json()
            self.plants = [plant for plant in plants if plant.get("devicesList")]
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
        self.get_actuator_url()

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_plantList_update, ())



if __name__ == "__main__":
    # cherrypy configuration
    conf = {"/": {
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on':True
        }
    }
    catalog_url = "http://127.0.0.1:8080/"
    adaptor_url = "http://127.0.0.1:8099/"
    operator_control = Operator_control(catalog_url, adaptor_url)

    cherrypy.config.update({'server.socket_port': 8095})
    webService = operator_control
    cherrypy.tree.mount(webService,'/',conf)
    cherrypy.engine.start()

    try:
        # Wait for 600 seconds
        for _ in range(600):
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Shutting down...")
        cherrypy.engine.stop()
    finally:
        cherrypy.engine.block()