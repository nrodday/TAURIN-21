import time
import configparser

from ripe.atlas.cousteau import (
    Measurement
)

config = configparser.ConfigParser()
config.read('config.ini')
print(config['ripe.account']['atlasapikey'])
print(config['traceroute.config']['target'])

measurement = Measurement(id=27955078)

while (measurement.status != "Stopped"):
    measurement = Measurement(id=27955078)
    print ("MSM status: "+measurement.status)
    print("Waiting till measurement is stopped!")
    time.sleep(5)

print("Measurement stopped!")