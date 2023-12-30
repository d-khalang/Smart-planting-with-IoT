import time
import requests
import json

class Device_connector():
    def __init__(self, catalog_url, plantConfig):
        self.catalog_url, self.plantConfig = catalog_url, plantConfig
        
    
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
                return "PUT request successful"
            else:
                return f"""POST: {postReq.text}
                PUT: {putReq.text}"""
        else:
            return f"Unkown response: {postReq_status}"
            


if __name__ == "__main__":
    catalog_url = "http://127.0.0.1:8080/"
    plantConfigFileName = "devices_configuration.json"

    with open(plantConfigFileName) as fp:
        plantConfig = json.load(fp)

    raspbery = Device_connector(catalog_url, plantConfig)

    t = 0
    while t < 600:
        if t%10 == 0:
            print(raspbery.registerer())
        time.sleep(1)
        t+=1


## to have as many as device connector for each plant you can
## instantiate as many raspbery class and register them