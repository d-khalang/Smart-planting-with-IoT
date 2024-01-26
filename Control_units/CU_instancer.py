import requests
import sched
import time
import json
from control_unit import Controler
import copy
import math

class CU_instancer():
    def __init__(self, catalog_url):
        self.catalog_url = catalog_url
        self.availableLevelsList = []
        self.PERIODIC_UPDATE_INTERVAL = 60  # seconds
        self.NOL_FOR_EACH_CONTROLER = 5  # number of levels that one control unit is in charge of 
        
        # Schedule updating the plant lists and plant kinds every 10 minutes
        # Creating self.plants and self.plantKinds
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantList_update, ())
        self.scheduler.run(blocking=False)

        # After updating the plantsList following with the update of the LevelsList
        # Creating the controlers for every few levels
        self.controler_creator()

        # Schedule the subscriptions for the controlers
        self.scheduler.enter(0, 2, self.subscribe_to_all, ())
        self.scheduler.run()

    


    # For each controler, subscribing to its levels dynamically
    # Its according to arrangment of the levels. Each controler is responsible for every few levels 
    def subscribe_to_all(self):
        # To create new controlers if new levels have been added
        self.check_levels_and_controlers()

        # Creating a copy of the available levels, to avoid changing the list itself
        tempAvailableLevelsList = copy.deepcopy(self.availableLevelsList)
        
        # For each controler
        for i in range (self.nOfControler):
            # Levels of the specific controler are the few first levels of available levels 
            # (according to the number of levels each controler is responsible for)
            levels = tempAvailableLevelsList[:self.NOL_FOR_EACH_CONTROLER]

            # Function for subscribing to topics of all levels
            self.controlers[f"controler_{i}"].subscribe_main_topic(levels)
            print(f"controler_{i} subscribed to levels: {levels} (CU_instancer)")

            # Removing the already subscribed levels from the temporary available levels
            tempAvailableLevelsList = tempAvailableLevelsList[self.NOL_FOR_EACH_CONTROLER:]

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 2, self.subscribe_to_all, ())



    # Checking and creating controler if new levels are added which have no available controler
    def check_levels_and_controlers(self):
        newControlerNeeded = math.ceil(len(self.availableLevelsList)/self.NOL_FOR_EACH_CONTROLER) - len(self.controlers.keys())
        if newControlerNeeded != 0:
            print(f"{newControlerNeeded} is needed(CU_instancer)")
            for i in range(newControlerNeeded):
                controlerName = self.controlers.keys()[0] + "n"  # Not to contradict with previous names
                self.controlers[controlerName] = Controler() 

    
    def controler_creator(self):
        self.nOfControler = math.ceil(len(self.availableLevelsList)/self.NOL_FOR_EACH_CONTROLER)
        self.controlers = {}
        for i in range(self.nOfControler):
            controlerName = f"controler_{i}"
            self.controlers[controlerName] = Controler(self.catalog_url)
            print(f"Controler {controlerName} is created(CU_instancer)")


    # Updating the available level list
    def update_levelList(self):
        self.availableLevelsList = []
        for plant in self.plants:
            # Checking if the level is in the available levels' list
            # Checking if the plant includes any device 
            if plant["levelID"] not in self.availableLevelsList and len(plant["devicesList"]) > 0:
                self.availableLevelsList.append(plant["levelID"])
                print(f"Level {plant["levelID"]} is added(CU_instancer)")
        self.availableLevelsList.sort()


    # Updating the plant lists every 10 minutes
    def periodic_plantList_update(self):
        # Requesting to the catalog
        try:
            req_p = requests.get(self.catalog_url+"plants")
            print("Plant list is updated(CU_instancer)\n")
        
        except requests.exceptions.RequestException as e:
            return f"Error during GET request: {e}"
         
        self.plants = req_p.json()
        self.update_levelList()

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_plantList_update, ())


if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    cu_instancer = CU_instancer(catalog_url)
    
    for i in range(2400):
        time.sleep(1)