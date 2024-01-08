import cherrypy
import json
import datetime
import sched
import time

class WebCatalog():
    exposed = True
    def __init__(self, address):
        with open(address, 'r') as fptr:
            self.catalog = json.load(fptr)
        self.mainTopic = self.catalog["projectName"]   # Using the project name as the main topic for evey plant unit
        self.broker = self.catalog["broker"]
        self.plantKinds = self.catalog["plantKindList"]
        self.plants = self.catalog["plantsList"]


        # Schedule the cleanup task every 10 minutes
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_cleanup, ())
        self.scheduler.run(blocking=False)
    

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri)== 0:
            return "No valid url. Enter a valid url among: broker, devices, device/{id}, plants, plant/{levelID}/{plantID}, topic, plantkinds"
        else:
            path = uri[0].lower()

            ## Retrieve information about the message broker
            if path == "broker":
                return self.broker
            

            # Retrive information about devices
            elif path == "devices":
                return self.devices
            
            elif path == "device":
                ## checking if the url is a device id
                try:
                    deviceID = int(uri[1])
                except:
                    return "No device entered, go to device/{device id}"
                
                # The first device with that device ID
                theDevice = next(filter(lambda device: device["deviceID"] == deviceID, self.devices), None)
                if theDevice:
                    return theDevice
                else: return f"No device with id:{deviceID}"


            # Retrive information about plants
            elif path == "plants":
                return self.plants
            
            elif path == "plant":
                ## checking if the level and plant ID is included in the URL
                try:
                    levelID, plantID = int(uri[1]), int(uri[2])
                except:
                    return "Unkown levelId and plantID entered, go to plant/{level id}/{plant id}"

                # The first plant with that level and plant ID
                thePlant = next(filter(lambda plant: plant["levelID"] == levelID and plant["plantID"] == plantID, self.plants), None) 
                if thePlant:
                    return thePlant
                else: return f"No plant with levelId:{levelID} and plantID:{plantID}"

            # Retrive information about plant kinds
            elif path == "plantkinds":
                return self.plantKinds


            ## Retrieve information about the main topic, usful for the control units
            elif path == "topic":
                return self.mainTopic
            
            else:
                return "No valid url. Enter a valid url among: broker, devices, device/{id}, plants, plant/{levelID}/{plantID}, topic, plantkinds"

                


    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, *uri, **params):
        if len(uri) == 0:
            return """Adding a plant unit -> /plants,
            Adding a device to plants -> /devices
            Adding a user -> /users
            Adding a new kind of plant -> /plantkinds"""
        else:
            path = uri[0].lower()
            ### Adding a Device
            if path == 'devices':
                deviceAdded = False
                newDevice = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                newDevice["lastUpdate"] = theTime
                
                #checking if the device exists in devices list
                if any(device["deviceID"] == newDevice["deviceID"] for device in self.devices):
                    return "Device already exists", 202    

                ## adding the device in the plant which owns the device
                levelID, plantID = newDevice["deviceLocation"]["levelID"], newDevice["deviceLocation"]["plantID"]
                for plant in self.plants:
                    if plant["levelID"] == levelID and plant["plantID"] == plantID:
                        plant["devicesList"].append(newDevice)
                        deviceAdded = True
                        
                        ## updating the main time of the catalog
                        self.catalog["lastUpdate"] = theTime
                        break

                ## return the status of the operation
                if deviceAdded:
                    self.deviceGetter()
                    # Rewrite the json catalog file
                    self.save_catalog()
                    return "Item is added successfully", 201
                else:
                    return "Not successfull"
                # return self.catalog

            
            ### Adding a plant
            elif path == "plants":
                newPlant = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Updating the time stamp of the plant
                newPlant["lastUpdate"] = theTime

                # Updating the time stamp of the devices inside the plant
                for device in newPlant['devicesList']:
                    device["lastUpdate"] = theTime

                #checking if the Plant exists in plants list
                if any(plant["levelID"] == newPlant["levelID"] and plant["plantID"] == newPlant["plantID"] for plant in self.plants):
                    return "plant already exists", 202
                else:
                    self.plants.append(newPlant)
                    self.deviceGetter()
                    ## updating the main time of the catalog
                    self.catalog["lastUpdate"] = theTime
                    # Rewrite the json catalog file
                    self.save_catalog()
                    return "Plant is added successfully", 201

            ### Adding a User
                
            ### Adding a Plant kind
            elif path == "plantkinds":
                newPlantKind = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                newPlantKind["lastUpdate"] = theTime

                #checking if the Plant kind exists in plantkinds list
                if any(plantKind["plantKind"].lower() == newPlantKind["plantKind"].lower() for plantKind in self.plantKinds):
                    return "Same kind of plant already exists", 202
                else:
                    self.plantKinds.append(newPlantKind)
                    ## updating the main time of the catalog
                    self.catalog["lastUpdate"] = theTime
                    # Rewrite the json catalog file
                    self.save_catalog()
                    return "Plant is added successfully", 201

            else:
                return """Adding a plant unit -> /plants,
            Adding a device to plants -> /devices
            Adding a user -> /users
            Adding a new kind of plant -> /plantkinds"""




    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def PUT(self, *uri, **params):
        if len(uri) == 0:
            return """Updating a plant unit -> /plants,
            Updating a device to plants -> /devices
            Updating a user -> /users
            Updating a new kind of plant -> /plantkinds"""
        else:
            path = uri[0].lower()
            ### Updating a device
            if path == 'devices':
                deviceUpdated = False
                newDevice = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                newDevice["lastUpdate"] = theTime
                

                
                ## adding the device in the plant which owenes the device
                levelID, plantID = newDevice["deviceLocation"]["levelID"], newDevice["deviceLocation"]["plantID"]
                plantUpdated = False
                for plant in self.plants:
                    if plant["levelID"] == levelID and plant["plantID"] == plantID:
                        for i in range(len(plant["devicesList"])):
                            if newDevice["deviceID"] == plant["devicesList"][i]["deviceID"]:
                                plant["devicesList"][i] = newDevice
                                plantUpdated = True

                        if not plantUpdated:
                            plant["devicesList"].append(newDevice)
                            deviceUpdated = True
                            

                ## return the status of the opperation
                if plantUpdated:
                    self.catalog["lastUpdate"] = theTime
                    self.deviceGetter()
                    # Rewrite the json catalog file
                    self.save_catalog()
                    return "Device is updated successfully in the corresponding plant section", 201
                
                elif deviceUpdated:
                    self.catalog["lastUpdate"] = theTime
                    self.deviceGetter()
                    # Rewrite the json catalog file
                    self.save_catalog()
                    return "The plant has been found and device is added to its devices", 201
                
                else:
                    return "Not succesfull, probably plant and device does not exist"
                # return self.catalog

            ### Updating a plant
            elif path == "plants":
                plantUpdated = False
                newPlant = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Updating the time stamp of the plant
                newPlant["lastUpdate"] = theTime

                # Updating the time stamp of the devices inside the plant
                for device in newPlant['devicesList']:
                    device["lastUpdate"] = theTime


                #checking if the Plant exists in plants list
                for plant in self.plants:
                    if plant["levelID"] == newPlant["levelID"] and plant["plantID"] == newPlant["plantID"]:
                        plant.update(newPlant)
                        plantUpdated = True
                        self.catalog["lastUpdate"] = theTime
                        self.deviceGetter()
                        # Rewrite the json catalog file
                        self.save_catalog()
                        return "plant is updated Succesfully", 201
                    
                if not plantUpdated:
                    return "Plant with the same level and plant Id does not exist"
                
            ### Updating a Plant kind
            elif path == "plantkinds":
                plantKindUpdated = False
                newPlantKind = cherrypy.request.json
                theTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                newPlantKind["lastUpdate"] = theTime

                #checking if the Plant kind exists in plantkinds list
                for plantKind in self.plantKinds:
                    if plantKind["plantKind"] == newPlantKind["plantKind"]:
                        plantKind.update(newPlantKind)
                        plantKindUpdated = True
                        # Rewrite the json catalog file
                        self.save_catalog()
                        return "Plant kind of is updated successfully", 201
                if not plantKindUpdated:
                    return "Plantkind with the same name does not exist"

            else:
                return """Updating a plant unit -> /plants,
                        Updating a device to plants -> /devices
                        Updating a user -> /users
                        Updating a new kind of plant -> /plantkinds"""


            ### Updating a User



    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def DELET(self, *uri, **params):
        if len(uri) != 0:
            path = uri[0].lower()

            # Removing a Plant
            if path == "plants":
                try:
                    levelID, plantID = params['levelID'], params['plantID']
                    plant_removed = False
                    for plant in self.plants:
                        if plant["levelID"] == levelID and plant["plantID"] == plantID:
                            self.plants.remove(plant)
                            plant_removed = True
                    
                    if plant_removed:
                        self.deviceGetter()
                        return "The plant is removed successfully"
                except KeyError:
                    return "Enter 'levelID' and 'plantID' as parameters"
        else: 
            return "To delete a plant go to /plants"


    ## creating self.devices which carries all the devices
    def deviceGetter(self):
        self.devices = []
        for plant in self.plants:
            for device in plant["devicesList"]:
                self.devices.append(device)


    # updating the plants' devices with the one with timestamps erlier than 1 hour
    def periodic_cleanup(self):
        THRESHOLD = 1 #hour
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        one_hour_ago = datetime.datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=THRESHOLD)

        for plant in self.plants:
            plant['devicesList'] = [device for device in plant['devicesList']
                                    if datetime.datetime.strptime(device.get('lastUpdate', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S") >= one_hour_ago]

        ## creating self.devices which carries all the devices
        self.deviceGetter() 

        # Update the catalog timestamp
        self.catalog["lastUpdate"] = current_time

        # Rewrite the json catalog file
        self.save_catalog()

        # Reschedule the periodic cleanup every 10 minutes
        self.scheduler.enter(600, 1, self.periodic_cleanup, ())


    # Rewriting the catalog
    def save_catalog(self):
        try:
            with open('catalog.json', 'w') as fptr:
                json.dump(self.catalog, fptr, indent=4)
        except Exception as e:
            print(f"Error saving catalog: {e}")

if __name__ == "__main__":
    conf = {"/": {
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on':True
        }
    }
    webService = WebCatalog('catalog.json')
    cherrypy.tree.mount(webService,'/',conf)
    cherrypy.engine.start()
    cherrypy.engine.block()