import requests, sched, time, json
from datetime import date, datetime
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton


class TeleBotDataManager():
    def __init__(self, operator_control_url):
        self.operator_control_url = operator_control_url
        self.plantsDict = None
        self.PERIODIC_UPDATE_INTERVAL = 600  # seconds
        
        # Schedule updating the plants dict PERIODIC_UPDATE_INTEVERVAL seconds
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(0, 1, self.periodic_plantDict_update, ())
        self.scheduler.run(blocking=False)
        

    def get_available_plants_name(self):
        return self.plantsDict.keys()

    # Getting the age of the plant
    def get_plant_age(self, levelPlantID):
        # 7 weeks to be ripe
        for channelID, plant in self.plantsDict.items():
            if channelID == levelPlantID:
                plantingDate = plant["plantingDate"]

        today = date.today()

        # Convert the format from string to date obj
        theDate = datetime.strptime(plantingDate, "%Y-%m-%d").date()

        # Calculate the difference in days
        difference = (today - theDate).days
        FULL_GROWING_TIME = 50 # 7 weeks
        dayUntilReady = FULL_GROWING_TIME - difference

        return dayUntilReady



    # Getting sensing data from thingSpeak which is gattered in operator control
    def get_sensors_data(self, levelPlantID):
        try:
            req_g = requests.get(f"{self.operator_control_url}sensing_data/{levelPlantID}")
            sensingDataDict = req_g.json()
            print("Current sensing data recieved")
            return sensingDataDict

        except requests.exceptions.RequestException as e:
            print(f"failed to get current sensing data from operator control. Error:{e}")


    # Getting actuation devices' status
    def get_actuators_status(self, levelPlantID):
        deviceStatusesDict = {}
        for channelID, plant in self.plantsDict.items():
            if channelID == levelPlantID:
                for device in plant["devicesList"]:
                    deviceStatusesDict[device["deviceName"]] = device["deviceStatus"]

        return deviceStatusesDict


    def periodic_plantDict_update(self):
        try:
            req_g = requests.get(self.operator_control_url+"plants")
            self.plantsDict = req_g.json()
            print("Plants dictionary recieved")

        except requests.exceptions.RequestException as e:
            print(f"failed to get plants dictionary from operator control. Error:{e}")

        # Schedul the next update
        self.scheduler.enter(self.PERIODIC_UPDATE_INTERVAL, 1, self.periodic_plantDict_update, ())


class TeleBot():
    def __init__(self, token, operator_control_url, ownershipFileName):
        self.token = token
        self.ownershipFileName = ownershipFileName
        self.botManager = TeleBotDataManager(operator_control_url)
        self.bot = telepot.Bot(self.token)
        callback_dict = {'chat': self.on_chat_message,
                         'callback_query': self.on_callback_query}
        MessageLoop(self.bot, callback_dict).run_as_thread()

        # Read the current plant ownership from its file
        with open(self.ownershipFileName, 'r') as fp:
            self.ownershipDict = json.load(fp)

        self.availablePlants = []
        self.find_available_plants()
        

    
    def find_available_plants(self):
        self.availablePlants = []
        plantNames = self.botManager.get_available_plants_name()
        for plantName in plantNames:
            if plantName not in self.ownershipDict.values():
                self.availablePlants.append(plantName)

    # Triggered when recieving text messages
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        cmd = msg['text']

        if cmd == "/start":
            self.bot.sendMessage(chat_id, "Wellcome to SkyFarming bot")

        elif cmd == "/menu":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Track your plant', callback_data='Track your plant'),
                     InlineKeyboardButton(text='Get a plant', callback_data='Get a plant')]
               ])

            self.bot.sendMessage(chat_id, "You own a plant or need a new one?", reply_markup=keyboard)
        else:
            self.bot.sendMessage(chat_id, "Sorry, I couldn't help you with that!!")


    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print(query_id, from_id, query_data)

        if query_data == "Get a plant":
            if self.availablePlants == []:
                self.bot.sendMessage(from_id, "Ops! No plant available :(")
            
            else:
                my_inline_keyboard = []
                for plantName in self.availablePlants:
                    my_inline_keyboard.append([InlineKeyboardButton(text=f'plant {plantName}', callback_data=f"get{plantName}")])
    
                keyboard2 = InlineKeyboardMarkup(inline_keyboard=my_inline_keyboard)

                self.bot.sendMessage(from_id, "Available plants:", reply_markup=keyboard2)

        # When getting a plant button is triggered
        elif query_data.startswith('get') and query_data.lstrip('get') in self.availablePlants:
            # When the user owns a plant
            what = self.ownershipDict.get(from_id)
            if self.ownershipDict.get(str(from_id)):
                self.bot.sendMessage(from_id, "You already own a plant")

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Track your plant', callback_data='Track your plant')]
               ])

                self.bot.sendMessage(from_id, "Try tracking yours", reply_markup=keyboard)
                
            # When user does not own any plants so will get it
                # something worng here
            elif str(from_id) not in self.ownershipDict.keys():
                self.ownershipDict[str(from_id)] = query_data.lstrip('get')
                self.find_available_plants()
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Track your plant', callback_data='Track your plant')]
               ])

                self.bot.sendMessage(from_id, "Congrats!! It's now yours :)", reply_markup=keyboard)
                
            # when they own another plant
            elif self.ownershipDict.get(str(from_id)) != None and self.ownershipDict.get(from_id) != query_data.lstrip('get'):
                self.bot.sendMessage(from_id, "You are not the owner of this plant. Sorry :(")

        elif query_data == "Track your plant":
            if str(from_id) in self.ownershipDict.keys():
                self.bot.sendMessage(from_id, "Your plant information:")

                # get info to show how many days remain until harvesting
                dayUntilReady = self.botManager.get_plant_age(self.ownershipDict[str(from_id)])
                self.bot.sendMessage(from_id, f"Your plant will be ready to harvest in {str(dayUntilReady)} days")

                sensingData = self.botManager.get_sensors_data(self.ownershipDict[str(from_id)])
                # Convert the dictionary into a string format
                sensing_data_str = "\n".join([f"{sensor_kind}: {value}" for sensor_kind, value in sensingData.items()])
                self.bot.sendMessage(from_id, sensing_data_str)
                
                statusData = self.botManager.get_actuators_status(self.ownershipDict[str(from_id)])
                # Convert the dictionary into a string format
                status_data_str = "\n".join([f"{deviceName}: {status}" for deviceName, status in statusData.items()])
                self.bot.sendMessage(from_id, status_data_str)
            
            else:
                self.bot.sendMessage(from_id, "Sorry, you don't have any plant :(")



    def save_ownership_dict(self):
        with open(self.ownershipFileName, 'w') as fp:
            json.dump(self.ownershipDict, fp, indent=4)
        


if __name__ == "__main__":
    operator_control_url = "http://127.0.0.1:8095/"
    ownershipFileName = "plant_ownership.json"
    # print(botManager.get_actuators_status("11"))
    # print("\n\n")
    # print(botManager.get_sensors_data("11"))
    token = "00000000"
    bot = TeleBot(token, operator_control_url, ownershipFileName)
    

    while 1:
        time.sleep(10)
        bot.save_ownership_dict()

    bot.save_ownership_dict()
