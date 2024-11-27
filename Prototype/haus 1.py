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

dht22 = dht.DHT22(machine.Pin(10))

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"
MQTT_BROKER = "test.mosquitto.org"
CLIENT_ID = hexlify(unique_id())
LITUR = b"2703litur"

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
do_connect()




mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(neop)
mqtt_client.connect()
mqtt_client.subscribe(LITUR)


async def main_loop():
    while True:
        mqtt_client.check_msg()
        await asyncio.sleep(1)

asyncio.run(main_loop())