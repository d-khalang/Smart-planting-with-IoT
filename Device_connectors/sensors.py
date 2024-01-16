import random
import time 



class TempSen():
    def __init__(self):  # ?device id can be added
        self.MIN_TEMP = 0
        self.MAX_TEMP = 65
        self.unit = "Cel"
        self.senKind = "temperature"

    def generate_data(self):
            value = random.randint(self.MIN_TEMP, self.MAX_TEMP)

            return value
    
    def get_info(self):
        return (self.senKind, self.unit)



class LightSen():
    def __init__(self):
        self.MIN_LIGHT = 50
        self.MAX_LIGHT = 350
        self.unit = "μmol/m²/s"
        self.senKind = "light"

    def generate_data(self):
            value = random.randint(self.MIN_LIGHT, self.MAX_LIGHT)

            return value
    
    def get_info(self):
        return (self.senKind, self.unit)
    


class PHSen():
    def __init__(self):
        self.MIN_PH = 3.5
        self.MAX_PH = 8.5
        self.unit = "Range"
        self.senKind = "PH"

    def generate_data(self):
            value = round(random.uniform(self.MIN_PH, self.MAX_PH), 2)

            return value
    
    def get_info(self):
        return (self.senKind, self.unit)


class WaterLevelSen():
    def __init__(self):
        self.MIN_DISTANCE = 1.5
        self.MAX_DISTANCE = 0.2
        self.unit = "Meter"
        self.senKind = "waterLevel"
        
    def generate_data(self):
        value = round(random.uniform(self.MIN_DISTANCE, self.MAX_DISTANCE), 2)

        return value
        
    def get_info(self):
        return (self.senKind, self.unit)
        

    
class TDSSen():
    def __init__(self):
        self.MIN_TDS = 50
        self.MAX_TDS = 1000
        self.unit = "bpm"
        self.senKind = "TDS"
        
    # generation of data base on seeding, vegetation, and flowering stage will be implemented
    def generate_data(self):
        value = round(random.uniform(self.MIN_TDS, self.MAX_TDS), 2)

        return value

    def get_info(self):
        return (self.senKind, self.unit)
