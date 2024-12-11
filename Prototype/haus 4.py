from binascii import hexlify
from umqtt.simple import MQTTClient
from machine import Pin, unique_id, ADC, PWM
from time import sleep_ms
from servo import Servo
import asyncio, json
import ujson
import time
import machine
import dht
from machine import Pin, PWM


MQTT_BROKER = "10.201.48.103" 
CLIENT_ID = hexlify(unique_id())

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"

# Main topic eru augu og Senu switch
# Fyrsti stafur er annað hvort H = Hægri eða V = Vinstri EÐA K = Kjalki EÐA U = Haus EÐA S = Háls
# Annar stafur er annað hvort
# M = Hreyfa (Move) eða S = Hraði (Speed) eða A = Auga
MAIN_TOPIC = b"0307LOKA"
HM_TOPIC = b"0307HM"
VM_TOPIC = b"0307VM"
KM_TOPIC = b"0307KM"
UM_TOPIC = b"0307UM"
SM_TOPIC = b"0307SM"
HA_TOPIC = b"0307HA"
VA_TOPIC = b"0307VA"

#Allt sem byrjar á 0307 eru skilaboð frá Node-RED, 2703 eru skilaboð frá hauskúpunni, 2709 eru skilaboð frá PI-2 skjánum
API = b"0307API"
start_sena = b"0307StartSena"
senda_API = b"2703sendaAPI"
skjar_buinn_humidity = b"2709buinn_humidity"
senda_humidity = b"2703Buinn"
skjar_buinn_vedur = b"2709buinn_vedur"

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    print("Running")
    
do_connect()
#stilli i_gangi breytuna
global i_gangi
i_gangi = False

dht22 = dht.DHT22(machine.Pin(2))

# Klasi fyrir mótorana
# Heldur utan um minnst og mest sem mótor getur hreyft
# normal er þegar mótorinn er "venjulegur" / upprétt
# Tekur inn (mótorinn sjálfan, minnst, mest, upprétt)
class Motor:
    def __init__(self, motor, minnst, mest, normal):
        self.motor = motor
        self.min = minnst
        self.max = mest
        self.normal = normal
    
    def hreyfa_motor(self, i):
        self.motor.write_angle(i)

# Klasi fyrir augun sem tekur inn peruna hjá auganu
class Auga:
    def __init__(self, raudur_pin, graenn_pin, blar_pin, freq=1000):
        self.freq = freq
        self._raudur = PWM(Pin(raudur_pin), freq=freq)
        self._graenn = PWM(Pin(graenn_pin), freq=freq)
        self._blar = PWM(Pin(blar_pin), freq=freq)
    
    def breyta_lit(self, rgb):
        rgb = ujson.loads(rgb)
        self._raudur.duty_u16(int((rgb["r"] / 255) * 65535))
        self._graenn.duty_u16(int((rgb["g"] / 255) * 65535))
        self._blar.duty_u16(int((rgb["b"] / 255) * 65535))

# Mótorarnir sjálfir
vinstri_motor = Servo(Pin(5))
haegri_motor = Servo(Pin(4))
haus_motor = Servo(Pin(6))
hals_motor = Servo(Pin(7))
kjalki_motor = Servo(Pin(15))

# Mótorarnir í Motor klasanum
# Nota þessa
HondLeft = Motor(vinstri_motor, 0, 70, 70)
HondRight = Motor(haegri_motor, 25, 100, 0)
Haus = Motor(haus_motor, 0, 180, 90)
Hals = Motor(hals_motor, 0, 180, 67)
Kjalki = Motor(kjalki_motor, 55, 100, 65)

# Auga Litir í RGB format
AugaH = Auga(40, 39, 41) 

#Auga fyrir senuna
Lblar = Pin(35, Pin.OUT)
Lraudur = Pin(36, Pin.OUT)
Lgraenn = Pin(37, Pin.OUT)

# Hátalari uppsetning
from lib.dfplayer import DFPlayer
df = DFPlayer(2)
df.init(tx=16, rx=17)

# Tekur inn file og spilar það
# Verður að vera async
async def spila_hljod(file1, file2):
    await df.volume(30)
    await df.play(file1, file2)
    await asyncio.sleep_ms(0)
    
async def sena1(location, humidity_skynjari):
    global hitastig, humidity, vedur, i_gangi
    #ef að senan var keyrð frá skynjaranum, þá sendir það upplýsingar úr skynjaranum, ef ekki úr global variable
    if location == "skynjari": 
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity_skynjari, "vedur": vedur}))
    else:
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity, "vedur": vedur}))
    
    asyncio.create_task(spila_hljod(1,2))
    print("ding")
    i_gangi = True

async def skynjari():
    global humidity, i_gangi
    while True:
        try:
            # Trigger measurement
            dht22.measure()
            #temperature = dht22.temperature()  # In Celsius
            raki = dht22.humidity()       # Relative humidity

            # Print the values
            #print("Temperature: {:.1f}°C".format(temperature))
            print("Humidity: {:.1f}%".format(raki))

            #Ef að rakinn er hár og senan er ekki í gangi þá keyrir hann senuna
            if raki > 70 and i_gangi == False:
                #runna start dæminu
                asyncio.create_task(sena1("skynjari", raki))
                humidity = raki

        except OSError as e:
            print("Failed to read sensor data:", e)
        await asyncio.sleep(2)  # You need a little wait for stable readings

async def sena_humidity(humidity):
    await asyncio.sleep(2) 
    await spila_hljod(1, 3)
    await asyncio.sleep(0.5) 
    #hreyfir hendur einu sinni fyrir hverja 10% af raka
    for i in range(int(humidity // 10)):
        Lraudur.value(0)
        Lblar.value(1)
        Lgraenn.value(0)
        HondLeft.hreyfa_motor(70) 
        await asyncio.sleep(0.2)
        Lraudur.value(0)
        Lblar.value(0)
        Lgraenn.value(0)
        HondLeft.hreyfa_motor(0) 
        await asyncio.sleep(0.2) 
    

    #sendir skilaboð í skjáinn að það sé búið að hreyfa eftir raka 
    mqtt_client.publish(senda_humidity, ujson.dumps({"hitastig": True}))
    print("Búinn að hreyfa eftir humidity")
  
async def sena_vedur(vedur, hitastig):
    global i_gangi
    await asyncio.sleep(2) 
    #Eftir því hvaða veður það er þá spilar það áhveðin hljóð
    if vedur == "Rain" or vedur == "Drizzle":
        asyncio.create_task(spila_hljod(3, 4))
        Lraudur.value(1)
        Lblar.value(0)
        Lgraenn.value(0)
        await asyncio.sleep(0.5) 
        asyncio.create_task(spila_hljod(2, 4))
        
    elif vedur == "Clouds":
        asyncio.create_task(spila_hljod(3,1))
        Lraudur.value(1)
        Lblar.value(1)
        Lgraenn.value(1)
        await asyncio.sleep(0.5) 
        asyncio.create_task(spila_hljod(2,1))
        
    elif vedur == "Clear":
        asyncio.create_task(spila_hljod(3,2))
        Lraudur.value(1)
        Lblar.value(0)
        Lgraenn.value(1)
        await asyncio.sleep(0.5)
        asyncio.create_task(spila_hljod(2,2))
        
    elif vedur == "Snow":
        asyncio.create_task(spila_hljod(3,3))
        
        Lraudur.value(0)
        Lblar.value(1)
        Lgraenn.value(0)
        await asyncio.sleep(0.5)
        asyncio.create_task(spila_hljod(2,3))
        
    for i in range(abs(int(hitastig))):
        HondRight.hreyfa_motor(70)
        Lraudur.value(1)
        Lblar.value(1)
        Lgraenn.value(0)
        await asyncio.sleep(0.2)
        HondRight.hreyfa_motor(25)
        Lraudur.value(0)
        Lblar.value(0)
        Lgraenn.value(0)
        await asyncio.sleep(0.2)
    print("Búinn að hreyfa eftir veðri")
    i_gangi = False
    
def fekk_skilabod(topic, skilabod):
    # Stilli global variables fyrir veður gögnin, léttara þannig
    
    global API_Data, hitastig, humidity, vedur, i_gangi
    # Breyta skilaboði og topic úr bytes í eitthvað lesanlegt t.d. int, str
    
    
    # Ef að senan er ekki í gangi þá kíkir það hvort að skilaboðin séu tengd því
    
    #Þegar skjárinn er búinn að birta raka þá keyrir þetta
    if topic == skjar_buinn_humidity:
        asyncio.create_task(sena_humidity(humidity))

    #Þegar skjárinn er búinn að birta hitastig þá keyrir þetta
    elif topic == skjar_buinn_vedur:
        asyncio.create_task(sena_vedur(vedur, hitastig))
        
    # Topic til að hreyfa hægri hendi
    elif topic == HM_TOPIC:
        print("hægri", skilabod)
        HondRight.hreyfa_motor(int(skilabod))
    
    # Topic til að hreyfa vinstri hendi
    elif topic == VM_TOPIC:
        print("vinstri", skilabod)
        HondLeft.hreyfa_motor(int(skilabod))
        
    # Topic til að hreyfa kjálkann
    elif topic == KM_TOPIC:
        print("kjalki", skilabod)
        Kjalki.hreyfa_motor(int(skilabod))

    # Topic til að hreyfa Hausinn
    elif topic == UM_TOPIC:
        print("haus", skilabod)
        Haus.hreyfa_motor(int(skilabod))
        
    # Topic til að hreyfa hálsinn
    elif topic == SM_TOPIC:
        print("háls", skilabod)
        Hals.hreyfa_motor(int(skilabod))

    # Breyta lit á hægri auga
    elif topic == HA_TOPIC:
        print("RGB Hægri auga", skilabod)
        AugaH.breyta_lit(skilabod)
        
    elif i_gangi == False:
        # Fær API gögn og geymir, keyrir ef X
        if topic == API:
            message = ujson.loads(skilabod)
            print("Fékk API")
            #Vinnur úr API'inu
            hitastig = message["main"]["temp"]
            humidity = message["main"]["humidity"]
            vedur = message["weather"][0]["main"]
            #Ef að það er X mikið hitastig þá keyrir hann senuna
            if hitastig > 15 or hitastig < 1:
                asyncio.create_task(sena1("api", 1))
                print(f"Ég er að runna vegna þess að það er: {hitastig}°C")
            # Ef að það er X veður þá keyrir hann senuna
            elif vedur in ("Rain", "Snow", "Drizzle"):
                asyncio.create_task(sena1("api", 1))
                print(f"Ég er að runna vegna þess að það er: {vedur}")

        # Keyrir senuna
        elif topic == start_sena:
            asyncio.create_task(sena1("start", 1))
            

#fleiri MQTT stillingar
mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(fekk_skilabod)
mqtt_client.connect()

# Tengja við öll Topic
mqtt_client.subscribe(MAIN_TOPIC)
mqtt_client.subscribe(HM_TOPIC)
mqtt_client.subscribe(VM_TOPIC)
mqtt_client.subscribe(KM_TOPIC)
mqtt_client.subscribe(UM_TOPIC)
mqtt_client.subscribe(SM_TOPIC)
mqtt_client.subscribe(KM_TOPIC)
mqtt_client.subscribe(HA_TOPIC)
mqtt_client.subscribe(VA_TOPIC)
mqtt_client.subscribe(API)
mqtt_client.subscribe(start_sena)
mqtt_client.subscribe(skjar_buinn_humidity)
mqtt_client.subscribe(skjar_buinn_vedur)

# Aðalkóði
# Les og sendir skilaboð
# Beinagrind er keyrð hér
async def main():
    asyncio.create_task(skynjari())
    # Hvar allt gerist
    while True:    
        # Leita af skilaboði
        mqtt_client.check_msg()
        #kveiki á skynjaranum, látum hann runna á 2 sekúnda fresti
        
        # Bíða í 0.01 sec
        await asyncio.sleep(0.01)            
# Starta program

asyncio.run(main())

