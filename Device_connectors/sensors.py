import random
import time 



class TempSen():
    def __init__(self):  # ?device id can be added
        self.MIN_TEMP = 0
        self.MAX_TEMP = 65
    
    def generate_data(self):
         value = random.randint(self.MIN_TEMP, self.MAX_TEMP)

         return value



class LightSen():
    def __init__(self) -> None:
        pass


