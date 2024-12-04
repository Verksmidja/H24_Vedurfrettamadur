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

MQTT_BROKER = "10.201.48.103" 
CLIENT_ID = hexlify(unique_id())

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"

# Main topic eru augu og Senu switch
# Fyrsti stafur er annað hvort H = Hægri eða V = Vinstri
# Annar stafur er annað hvort
# M = Hreyfa (Move) eða S = Hraði (Speed) eða A = Auga
MAIN_TOPIC = b"0307LOKA"
HM_TOPIC = b"0307HM"
HS_TOPIC = b"0307HS"
VM_TOPIC = b"0307VM"
VS_TOPIC = b"0307VS"
HA_TOPIC = b"0307HA"
LA_TOPIC = b"0307LA"
#Allt sem byrjar á 0307 eru skilaboð frá Node-RED, 2703 eru skilaboð frá hauskúpunni, 2709 eru skilaboð frá PI-2 skjánum
API = b"0307API"
start_sena = b"0307StartSena"
senda_API = b"2703sendaAPI"
skjar_buinn_humidity = b"2709buinn_humidity"
sena_humidity = b"2703Buinn"
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
    
do_connect()

i_gangi = False
dht22 = dht.DHT22(machine.Pin(10))

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
    def __init__(self, raudur, graenn, blar):
        self._raudur = raudur
        self._graenn = graenn
        self._blar = blar
    
    
    # Fall til að breyta um lit á perunni
    def breyta_lit(self, rgb):
        
        #rgb = [litur for litur in json.loads(rgb).values()]
        rgb = json.loads(rgb)
        
        self._raudur.value(0)
        self._graenn.value(0)
        self._blar.value(255)
        

# Mótorarnir sjálfir
vinstri_motor = Servo(Pin(5))
haegri_motor = Servo(Pin(4))
haus_motor = Servo(Pin(6))
hals_motor = Servo(Pin(7))
kjalki_motor = Servo(Pin(15))

# Mótorarnir í Motor klasanum
# Nota þessa
HondLeft = Motor(vinstri_motor, 0, 70, 70)
HondRight = Motor(haegri_motor, 0, 100, 0)
Haus = Motor(haus_motor, 0, 180, 90)
Hals = Motor(hals_motor, 0, 180, 67)
Kjalki = Motor(kjalki_motor, 65, 100, 65)

# Auga Litir
Lblar = Pin(35, Pin.OUT)
Lraudur = Pin(36, Pin.OUT)
Lgraenn = Pin(37, Pin.OUT)
Rraudur = Pin(41, Pin.OUT)
Rblar = Pin(39, Pin.OUT)
Rgraenn = Pin(40, Pin.OUT)

# Augna litir í lista í RGB format
AugaH = Auga(Rraudur, Rgraenn, Rblar)
AugaL = Auga(Lraudur, Lgraenn, Lblar)


# Hátalari uppsetning
from lib.dfplayer import DFPlayer
df = DFPlayer(2)
df.init(tx=17, rx=16)
hljod_bylgjur = ADC(Pin(18), atten=ADC.ATTN_11DB)

# Tekur inn file og spilar það
# Verður að vera async
async def spila_hljod(file1, file2):
    await df.wait_available()
    await df.volume(15)
    await df.play(file1, file2)
    await asyncio.sleep_ms(0)
    
async def sena1(location, humidity_skynjari):
    global hitastig, humidity, vedur, i_gangi
    #ef að senan var keyrð frá skynjaranum, þá sendir það upplýsingar úr skynjaranum, ef ekki úr global variable
    if location == "skynjari": 
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity_skynjari, "vedur": vedur}))
    else:
        mqtt_client.publish(senda_API, ujson.dumps({"hitastig": hitastig, "humidity": humidity, "vedur": vedur}))
    
    #asyncio.create_task(spila_hljod(1,2))
    print("ding")
    i_gangi = True

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
    
    #Ef að rakinn er hár og senan er ekki í gangi þá keyrir hann senuna
    if raki > 70 and i_gangi == False:
        #runna start dæminu
        asyncio.create_task(sena1("skynjari", raki))
        humidity = raki
    #await asyncio.sleep(2)  # You need a little wait for stable readings

async def sena_humidity(humidity):
    asyncio.create_task(spila_hljod(1,3))
    
    #hreyfir hendur x mikið eftir raka
    
    #sendir skilaboð í skjáinn að það sé búið að hreyfa eftir raka 
    mqtt_client.publish(sena_humidity, ujson.dumps({"buinn": True}))
    print("Búinn að hreyfa eftir humidity")
  
async def sena_vedur(vedur, hitastig):
    #Eftir því hvaða veður það er þá spilar það áhveðin hljóð
    if vedur == "Rain":
        asyncio.create_task(spila_hljod(3,"rain.mp3"))
        asyncio.create_task(spila_hljod(2,"rain.mp3"))
        pass
    elif vedur == "Clouds":
        asyncio.create_task(spila_hljod(3,"cloudy.mp3"))
        asyncio.create_task(spila_hljod(2,"cloudy.mp3"))
        pass
    elif vedur == "Clear":
        asyncio.create_task(spila_hljod(3,"sun.mp3"))
        asyncio.create_task(spila_hljod(2,"sun.mp3"))
        pass
    elif vedur == "Snow":
        asyncio.create_task(spila_hljod(3,"snow.mp3"))
        asyncio.create_task(spila_hljod(2,"snow.mp3"))
        pass
    
    #hreyfa hendur x mikið eftir hitastigi
    print("Búinn að hreyfa eftir veðri")
    i_gangi = False
    
def fekk_skilabod(topic, skilabod):
    # Stilli global variables fyrir veður gögnin, léttara þannig
    
global API_Data, hitastig, humidity, vedur, i_gangi
    # Breyta skilaboði og topic úr bytes í eitthvað lesanlegt t.d. int, str
    
    
    # Ef að senan er ekki í gangi þá kíkir það hvort að skilaboðin séu tengd því
    if i_gangi == False:
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
                print(hitastig)
            # Ef að það er X veður þá keyrir hann senuna
            elif vedur in ("Rain", "Snow"):
                asyncio.create_task(sena1("api", 1))
                print(vedur)
                
        # Keyrir senuna
        elif topic == start_sena:
            asyncio.create_task(sena1("start", 1))
            
    #Þegar skjárinn er búinn að birta raka þá keyrir þetta
    elif topic == skjar_buinn_humidity:
        asyncio.create_task(sena_humidity(humidity))

    #Þegar skjárinn er búinn að birta hitastig þá keyrir þetta
    elif topic == skjar_buinn_vedur:
        asyncio.create_task(sena_vedur(vedur, hitastig))
        
    # Topic til að hreyfa hægri hendi
    elif topic == "0307HM":
        print("1")
        HondRight.hreyfa_motor(int(skilabod))
    
    # Topic til að hreyfa vinstri hendi
    elif topic == "0307VM":
        HondLeft.hreyfa_motor(int(skilabod))
        
    # Breyta lit á hægri auga
    elif topic == "0307HA":
        # Breyta augnarlit
        AugaH.breyta_lit(skilabod)
    

#fleiri MQTT stillingar
mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(fekk_skilabod)
mqtt_client.connect()

# Tengja við öll Topic
mqtt_client.subscribe(MAIN_TOPIC)
mqtt_client.subscribe(HM_TOPIC)
mqtt_client.subscribe(HS_TOPIC)
mqtt_client.subscribe(VM_TOPIC)
mqtt_client.subscribe(VS_TOPIC)
mqtt_client.subscribe(HA_TOPIC)
mqtt_client.subscribe(LA_TOPIC)
mqtt_client.subscribe(API)
mqtt_client.subscribe(start_sena)
mqtt_client.subscribe(skjar_buinn_humidity)
mqtt_client.subscribe(skjar_buinn_vedur)

# Aðalkóði
# Les og sendir skilaboð
# Beinagrind er keyrð hér
async def main():
    # Hvar allt gerist
    while True:    
        # Leita af skilaboði
        mqtt_client.check_msg()
        #kveiki á skynjaranum, látum hann runna á 2 sekúnda fresti
        asyncio.create_task(skynjari())
        # Bíða í 1 sec
        await asyncio.sleep(2)            
# Starta program

asyncio.run(main())
