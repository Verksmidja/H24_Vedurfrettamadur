from machine import Pin, unique_id
from binascii import hexlify
from time import sleep_ms
from umqtt.simple import MQTTClient
import network
import time
import ujson
import machine
import dht
import uasyncio as asyncio

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"
MQTT_BROKER = "10.201.48.103"
CLIENT_ID = hexlify(unique_id())
senda_API = b"2703sendaAPI"
skjar_buinn_humidity = b"2709buinn_humidity"
sena_humidity = b"2703Buinn"
skjar_buinn_vedur = b"2709buinn_vedur"

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
do_connect()
 
async def sena_humidity(humidity):
    #Birtir humidity (bara talan, kannski mynd af þoku?)
    
    print("Búinn að birta humidity")
    mqtt_client.publish(skjar_buinn_humidity, ujson.dumps({"buinn": True}))
    
async def sena_vedur(vedur, hitastig):
    if vedur == "Rain":
        #Mynd af rigningu ásamt hitastigi
        pass
    elif vedur == "Clouds":
        #Mynd af Skýjum ásamt hitastigi
        pass
    elif vedur == "Clear":
        #Mynd af Sól ásamt hitastigi
        pass
    elif vedur == "Snow":
        #Mynd af Snjó ásamt hitastigi
        pass
    
    mqtt_client.publish(skjar_buinn_vedur, ujson.dumps({"buinn": True}))

async def recieved(topic, msg):
    global hitastig, humidity, vedur
    message = ujson.loads(msg)
    if topic == senda_API:
        hitastig = message['hitastig']
        humidity = message['humidity']
        vedur = message['vedur']
        asyncio.create_task(sena_humidity(humidity))
        
    elif topic == sena_humidity:
        asyncio.create_task(sena_vedur(vedur, hitastig))
            
def on_message(topic, msg):
    asyncio.create_task(recieved(topic, msg))

mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(on_message)
mqtt_client.connect()
mqtt_client.subscribe(senda_API)
mqtt_client.subscribe(sena_humidity)

async def main_loop():
    while True:
        mqtt_client.check_msg()
        asyncio.create_task(skynjari())
        await asyncio.sleep(2)

asyncio.run(main_loop()