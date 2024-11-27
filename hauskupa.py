from binascii import hexlify
from umqtt.simple import MQTTClient
from machine import Pin, unique_id, ADC, PWM
from time import sleep_ms
import asyncio, json


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

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"

vedur_API_KEY = r"5c90fcc16948008b160ac6a0fb2bd272"

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
    

def fekk_skilabod(topic, skilabod):
    #global JSON breyta / skilaboðið í JSON format
    global JSON
    # Decoda skilaboð
    skilabod.decode()
    # Breyta í JSON format
    JSON = json.loads(skilabod)
    print(topic, skilabod)


# Tekur inn file og spilar það
# Verður að vera async
async def spila_hljod(file):
    
    await df.wait_available()
    await df.volume(15)
    await df.play(1, 1)
    await asyncio.sleep_ms(0)    

do_connect()

MQTT_BROKER = "broker.emqx.io" 
CLIENT_ID = hexlify(unique_id())

# Veður api

def 


# Main topic eru augu og Senu switch
# Fyrsti stafur er annað hvort H = Hægri eða V = Vinstri
# Annar stafur er annað hvort
# M = Hreyfa (Move) eða S = Hraði (Speed)
MAIN_TOPIC = b"0307LOKA"
HM_TOPIC = b"0307HM"
HS_TOPIC = b"0307HS"
VM_TOPIC = b"0307VM"
VS_TOPIC = b"0307VS"


mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(fekk_skilabod)
mqtt_client.connect()

# Tengja við öll Topic
mqtt_client.subscribe(MAIN_TOPIC)
mqtt_client.subscribe(HM_TOPIC)
mqtt_client.subscribe(HS_TOPIC)
mqtt_client.subscribe(VM_TOPIC)
mqtt_client.subscribe(VS_TOPIC)


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
Rraudur = Pin(38, Pin.OUT)
Rblar = Pin(39, Pin.OUT)
Rgraenn = Pin(40, Pin.OUT)

# Augna litir í lista í RGB format
AugaH = [Rraudur, Rgraenn, Rblar]
AugaL = [Lraudur, Lgraenn, Lblar]


# Hátalari uppsetning
from lib.dfplayer import DFPlayer
df = DFPlayer(2)
df.init(tx=17, rx=16)
hljod_bylgjur = ADC(Pin(18), atten=ADC.ATTN_11DB)

# global JSON breyta / skilaboð í json format
global JSON

# Aðalkóði
# Les og sendir skilaboð
# Beinagrind er keyrð hér
async def main():
    
    # Hvar allt gerist
    while True:    
        # Leita af skilaboði
        mqtt_client.check_msg()
        # Bíða í 1 sec
        await asyncio.sleep_ms(10)            
# Starta program

asyncio.run(main())
    


