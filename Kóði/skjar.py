import paho.mqtt.client as mqtt
import json
import asyncio
import RPi.GPIO as GPIO
from time import sleep
import os
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image


# Tenging fyrir WIFI

# Allt tengt MQTT
# Broker er Rasperry pi
# Allar mqtt tengingar eru á milli beinagrinds og Skjássins
WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"
MQTT_BROKER = "10.201.48.103"
CLIENT_ID = os.urandom(8).hex()
senda_API = "2703sendaAPI"
skjar_buinn_humidity = "2709buinn_humidity"
sena_humidity = "2703Buinn"
skjar_buinn_vedur = "2709buinn_vedur"

# Connect to Wi-Fi (handled automatically by Raspberry Pi OS)
print("Make sure your Raspberry Pi is connected to Wi-Fi.")

# GPIO Setup
GPIO.setmode(GPIO.BCM)

# MQTT Setup
mqtt_client = mqtt.Client(CLIENT_ID)
# Image configuration for weather display


# File path fyrir myndirnar
# 64x64 format
image_files = {
    "Rain": "/home/pi/Desktop/rain.jpeg",
    "Clouds": "/home/pi/Desktop/123.png",
    "Clear": "/home/pi/Desktop/sun.jpeg",
    "Snow": "/home/pi/Desktop/snow.jpeg"
}

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options=options)


# Breytur sem geyma hitastig, humidity og veður
# Kemur allt frá Veður API
# Humidity kemur frá Hita skynjara ef humidity er >70%
hitastig = None
humidity = None
vedur = None


# Async fall sem birtir humidity á skjáin
# Publish'ar á MQTT að skjárinn hefur birt mynd á skjáinn
async def publish_humidity():
    image = Image.open["/home/pi/Desktop/123456.jpg"]
    matrix.SetImage(image.convert('RGB'))
    mqtt_client.publish(skjar_buinn_humidity, json.dumps({"buinn": True}))
    print("Buinn ad birta humidity")


# Async fall sem birtir Mynd af veðri
# Notar vedur breytuna til að finna veðrið
async def publish_weather(vedur, hitastig):

    # Ef það er rigning
    # Prentar hitastig með upplýsingum
    if vedur == "Rain" or vedur "Drizzi":
        image = Image.open("/home/pi/Desktop/sun.jpeg")
        matrix.SetImage(image.convert('RGB'))
        print(f"Displaying Rain icon with temperature {hitastig}")

    # Ef það er Skýjað
    elif vedur == "Clouds":
        image = Image.open("/home/pi/Desktop/123.png")
        matrix.SetImage(image.convert('RGB'))

    # Ef það er Heiðskýrt
    elif vedur == "Clear":
        image = Image.open("/home/pi/Desktop/sun.jpeg")
        matrix.SetImage(image.convert('RGB'))

    # Ef það er að snjóa
    elif vedur == "Snow":
        image = Image.open("/home/pi/Desktop/snow.jpeg")
        matrix.SetImage(image.convert('RGB'))

    # Publish'ar til MQTT að skjárinn hefur birt myndina
    mqtt_client.publish(skjar_buinn_vedur, json.dumps({"buinn": True}))


# Tekur á móti MQTT skilaboðum
# Decode'ar skilaboðið með .decode()
# Gefur breytunum hitastig, humidity, vedur upplýsingar
async def received(topic, msg):

    # Global breytur til að nota í publish_weather() og publish_humidity()
    global hitastig, humidity, vedur

    # Decode'ar skilaboðið
    # Breytir úr JSON -> Dict
    message = json.loads(msg.decode())

    # Ef skilaboðið kemur frá Veður API
    if topic == senda_API:
        hitastig = message['hitastig']
        humidity = message['humidity']
        vedur = message['vedur']
        await publish_humidity()

    # Ef skilaboðið Beinagrindinni
    elif topic == sena_humidity:
        print("sena")
        await publish_weather(vedur, hitastig)


def on_message(client, userdata, msg):
    asyncio.run(received(msg.topic, msg.payload))


# Tengjast við MQTT
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)
mqtt_client.subscribe(senda_API)
mqtt_client.subscribe(sena_humidity)


# Main
# Async
# Leita á 2s fresti
async def main_loop():
    mqtt_client.loop_start()
    while True:
        # Replace `skynjari()` with your sensor reading logic if needed
        await asyncio.sleep(2)


# Bryja forrit
try:
    asyncio.run(main_loop())

# Ef ctrl+c er farið úr loop og hætt
except KeyboardInterrupt:
    print("Exiting program.")
    mqtt_client.loop_stop()
    GPIO.cleanup()