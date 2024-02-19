# Import Flask and other necessary modules
from flask import Flask, render_template, request, jsonify
import requests, json

# Your Flask app definition and other code...
app = Flask(__name__)


class UserAwareness():
    def __init__(self, operator_control_url, adaptor_url=None):
        self.operator_control_url = operator_control_url
        self.adaptor_url = adaptor_url

    def update_plantList(self):
        try:
            req_p = requests.get(self.operator_control_url + "plants")
            print("Plant list is updated (interface)\n")
            plants = req_p.json()
            self.plants = [plant for plant in plants.values() if plant.get("devicesList")]
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
            self.plants = []

    # Add getting info of adaptor address from the catalog and then request
    def get_channel_detail(self, channel_name):
        try:
            req_p = requests.get(self.operator_control_url + "channels_detail/"+channel_name)
            print("Thingspeak channel detail is updated (interface)\n")
            channel_detail = req_p.json()
            return channel_detail
        
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
            return None
        
        
    # Post the satatus of the device to the operator control
    def post_device_status(self, deviceDetailDict):
        try:
            req_po = requests.post(self.operator_control_url+"device_status", json=deviceDetailDict)
            print("Post request response form the operator control", req_po.text)

        except requests.exceptions.RequestException as e:
            print(f"failed to post the device status on operator control. Error:{e}")




    def get_plants(self):
        return self.plants
        

def get_button_class(status):
    if status == 'ON':
        return 'green'
    elif status == 'OFF':
        return 'blue'
    elif status == 'DISABLE':
        return 'red'
    else:
        return 'orange'  # Default color 

    
# Flask route to handle button clicks
@app.route('/send_status_message', methods=['POST'])
def send_status_message():
    deviceInfo = request.json
    # device_id = deviceInfo["deviceID"]
    status = deviceInfo["status"]

    # Call the send_status_message function with device_id and status here
    try:
        operator_control_url = "http://127.0.0.1:8095/"
        user_awareness = UserAwareness(operator_control_url)
        user_awareness.post_device_status(deviceInfo)

    except requests.exceptions.RequestException as e:
        print(f"failed to put the device status on operator control. Error:{e}")

    if status == "DISABLE":
        return jsonify({'message': f'{status} status not available at the moment'})
    return jsonify({'message': 'Status message sent successfully'})
    


# Route to display the index page
@app.route('/')
def index():
    operator_control_url = "http://127.0.0.1:8095/"
    user_awareness = UserAwareness(operator_control_url)
    user_awareness.update_plantList()
    plants = user_awareness.get_plants()
    return render_template('index.html', plants=plants)

# Dynamic route for each plant
@app.route('/plant/<int:level_id>/<int:plant_id>')
def plant_detail(level_id, plant_id):
    adaptor_url = "http://127.0.0.1:8099/"
    operator_control_url = "http://127.0.0.1:8095/"
    user_awareness = UserAwareness(operator_control_url, adaptor_url)
    user_awareness.update_plantList()
    plants = user_awareness.get_plants()
    channelDetail = user_awareness.get_channel_detail(str(level_id)+str(plant_id))
    channelID = channelDetail.get("channelId") if channelDetail else None
    # swapping the field number and data type
    fields = {v: k for k, v in channelDetail.get("fields", {}).items()} if channelDetail else {}
    
    
    # Find the plant with the specified plant_id
    plant = next((p for p in plants if p.get('plantID') == plant_id and p.get('levelID') == level_id), None)
    
    if plant:
        return render_template('plant_detail.html', plant=plant, channelID=channelID, fields=fields, get_button_class=get_button_class)
    else:
        return "Plant not found."

if __name__ == '__main__':
    
    app.run(debug=True)
