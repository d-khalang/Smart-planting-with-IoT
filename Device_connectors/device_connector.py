from MyMQTT import MyMQTT
from sensors import TempSen
import requests
import time

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
    def __init__(self, catalog_url, plantConfig, baseClientID,DCID, broker, port):
        self.catalog_url, self.plantConfig = catalog_url, plantConfig
        clientID = baseClientID+DCID+"_p"
        self.senPublisher = senPublisher(clientID, broker, port)

        levelID, plantID = DCID[0], DCID[1]
        self.msg = {
            "bn": f"skyFarming/{levelID}/{plantID}/sensor/",
            "e": [
                {
                    "n": 'senKind',
                    "u": 'unit',
                    "t": None,
                    "v": None
                }
            ]
        }

        ## sensors
        self.tempSen = TempSen()

    # Getting data from 'get_sen_data' and sending it to message broker
    def send_data(self):
        # Get the average data
        msg = self.get_sen_data()

        # Connect the publisher, publish the message and disconnect
        self.senPublisher.start()
        print("publisher started")
        time.sleep(1)
        self.senPublisher.publish(msg["bn"], msg)
        print("message published")
        time.sleep(1)
        self.senPublisher.stop()
        print("publisher stoped")



        # for now just tempreture sensor
    def get_sen_data(self):
        tempData = []

        # Generate a value every second
        for i in range(30):
            datum = self.tempSen.generate_data()
            tempData.append(datum)
            time.sleep(1)
        
        # Get the mean each 10 second
        avg = sum(tempData)/len(tempData)

        # Updating the message
        msg = self.msg
        msg['e'][0].update({"n":"temperature", "u":"Cel", "t":str(time.time()), "v":avg})
        msg["bn"] += "temperature"

        return msg


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
            





## to have as many as device connector for each plant you can
## instantiate as many raspbery class and register them
## create plant map