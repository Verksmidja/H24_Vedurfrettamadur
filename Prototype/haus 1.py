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
MQTT_BROKER = "10.201.48.103"
CLIENT_ID = hexlify(unique_id())
API = b"0307API"
start_sena = b"0307StartSena"
senda_API = b"2703sendaAPI"
skjar_buinn_humidity = b"2709buinn_humidity"
sena_humidity = b"2703Buinn"
skjar_buinn_vedur = b"2709buinn_vedur"

i_gangi = False

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
do_connect()

async def spila_hljod(file1, file2):
    await df.wait_available()
    await df.volume(15)
    await df.play(file1, file2)
    await asyncio.sleep_ms(0)

async def skynjari():
    global humidity, i_gangi
    try:
        # Trigger measurement
        dht22.measure()
        #temperature = dht22.temperature()  # In Celsius
        raki = dht22.humidity()       # Relative humidity

        # Print the values
        #print("Temperature: {:.1f}°C".format(temperature))
        print("Humidity: {:.1f}%".format(raki))

    except OSError as e:
        print("Failed to read sensor data:", e)
    
    if raki > 70 and i_gangi == False:
        #runna start dæminu
        asyncio.create_task(sena1("skynjari", raki))
        humidity = raki
    #await asyncio.sleep(2)  # You need a little wait for stable readings

async def sena1(location, humidity_skynjari):
    global hitastig, humidity, vedur, i_gangi
    if location == "skynjari": 
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity_skynjari, "vedur": vedur}))
    else:
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity, "vedur": vedur}))
    
    #asyncio.create_task(spila_hljod(1,2))
    print("ding")
    i_gangi = True
 
async def sena_humidity(humidity):
    #asyncio.create_task(spila_hljod(1,3))
    
    #hreyfir hendur x mikið eftir raka
    
    mqtt_client.publish(sena_humidity, ujson.dumps({"buinn": True}))
    print("Búinn að hreyfa eftir humidity")

async def sena_vedur(vedur, hitastig):
    
    if vedur == "Rain":
        #asyncio.create_task(spila_hljod(3,"rain.mp3"))
        #asyncio.create_task(spila_hljod(2,"rain.mp3"))
        pass
    elif vedur == "Clouds":
        #asyncio.create_task(spila_hljod(3,"cloudy.mp3"))
        #asyncio.create_task(spila_hljod(2,"cloudy.mp3"))
        pass
    elif vedur == "Clear":
        #asyncio.create_task(spila_hljod(3,"sun.mp3"))
        #asyncio.create_task(spila_hljod(2,"sun.mp3"))
        pass
    elif vedur == "Snow":
        #asyncio.create_task(spila_hljod(3,"snow.mp3"))
        #asyncio.create_task(spila_hljod(2,"snow.mp3"))
        pass
    
    #hreyfa hendur x mikið eftir hitastigi
    print("Búinn að hreyfa eftir veðri")
    i_gangi = False

async def recieved(topic, msg):
    global API_Data, hitastig, humidity, vedur, i_gangi
    message = ujson.loads(msg)
    if i_gangi == False:
        if topic == API:
            print("Fékk API")
            hitastig = message["main"]["temp"]
            humidity = message["main"]["humidity"]
            vedur = message["weather"][0]["main"]
            if hitastig > 15 or hitastitg < 1:
                asyncio.create_task(sena1("api", 1))
                print(hitastig)
            
            elif vedur in ("Rain", "Snow"):
                asyncio.create_task(sena1("api", 1))
                print(vedur)
            
        elif topic == start_sena:
            asyncio.create_task(sena1("start", 1))

        elif topic == skjar_buinn_humidity:
            asyncio.create_task(sena_humidity(humidity))

        elif topic == skjar_buinn_vedur:
            asyncio.create_task(sena_vedur(vedur, hitastig))
            
def on_message(topic, msg):
    asyncio.create_task(recieved(topic, msg))

mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(on_message)
mqtt_client.connect()
mqtt_client.subscribe(API)
mqtt_client.subscribe(start_sena)
mqtt_client.subscribe(skjar_buinn_humidity)
mqtt_client.subscribe(skjar_buinn_vedur)

async def main_loop():
    while True:
        mqtt_client.check_msg()
        asyncio.create_task(skynjari())
        await asyncio.sleep(2)

asyncio.run(main_loop())