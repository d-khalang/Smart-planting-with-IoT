# Import Flask and other necessary modules
from flask import Flask, render_template
import requests, json

# Your Flask app definition and other code...
app = Flask(__name__)


class User_awareness():
    def __init__(self, catalog_url, adaptor_url=None):
        self.catalog_url = catalog_url
        self.adaptor_url = adaptor_url

    def update_plantList(self):
        try:
            req_p = requests.get(self.catalog_url + "plants")
            print("Plant list is updated (interface)\n")
            plants = req_p.json()
            self.plants = [plant for plant in plants if plant.get("devicesList")]
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
            self.plants = []

    # Add getting info of adaptor address from the catalog and then request
    def get_channel_detail(self, channelName):
        try:
            req_p = requests.get(self.adaptor_url + "channels_detail")
            print("Thingspeak channel detail is updated (interface)\n")
            self.channelsDetail = req_p.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
        
        channelDetail = self.channelsDetail.get(channelName)
        return channelDetail

    def get_plants(self):
        return self.plants
        
    

# Route to display the index page
@app.route('/')
def index():
    catalog_url = "http://127.0.0.1:8080/"
    user_awareness = User_awareness(catalog_url)
    user_awareness.update_plantList()
    plants = user_awareness.get_plants()
    return render_template('index.html', plants=plants)

# Dynamic route for each plant
@app.route('/plant/<int:level_id>/<int:plant_id>')
def plant_detail(level_id, plant_id):
    catalog_url = "http://127.0.0.1:8080/"
    adaptor_url = "http://127.0.0.1:8099/"
    user_awareness = User_awareness(catalog_url, adaptor_url)
    user_awareness.update_plantList()
    plants = user_awareness.get_plants()
    channelDetail = user_awareness.get_channel_detail(str(level_id)+str(plant_id))
    channelID = channelDetail["channelId"]
    # swapping the field number and data type
    fields = {v: k for k, v in channelDetail["fields"].items()}
    
    
    # Find the plant with the specified plant_id
    plant = next((p for p in plants if p.get('plantID') == plant_id and p.get('levelID') == level_id), None)
    
    if plant:
        return render_template('plant_detail.html', plant=plant, channelID=channelID, fields=fields)
    else:
        return "Plant not found."

if __name__ == '__main__':
    
    app.run(debug=True)
