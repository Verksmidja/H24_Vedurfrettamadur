from binascii import hexlify
from umqtt.simple import MQTTClient
from machine import Pin, unique_id, ADC, PWM
from time import sleep_ms
from servo import Servo
import asyncio, json



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
VM_TOPIC = b"0307VM"
HA_TOPIC = b"0307HA"
LA_TOPIC = b"0307LA"



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
        
        print("asdasdasd", rgb)
        self._raudur.value('r')
        self._graenn.value('g')
        self._blar.value('b')
        


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
Rraudur = Pin(40, Pin.OUT)
Rblar = Pin(41, Pin.OUT)
Rgraenn = Pin(39, Pin.OUT)

# Augna litir í lista í RGB format
AugaH = Auga(Rraudur, Rgraenn, Rblar)
AugaL = Auga(Lraudur, Lgraenn, Lblar)


# Hátalari uppsetning
from lib.dfplayer import DFPlayer
df = DFPlayer(2)
df.init(tx=17, rx=16)
hljod_bylgjur = ADC(Pin(18), atten=ADC.ATTN_11DB)


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
    
    # Breyta skilaboði og topic úr bytes í eitthvað lesanlegt t.d. int, str
    skilabod = skilabod.decode()
    topic = topic.decode()
    print(topic, skilabod)
    
    # Topic til að hreyfa hægri hendi
    if topic == "0307HM":
        print("1")
        HondRight.hreyfa_motor(int(skilabod))
    
    # Topic til að hreyfa vinstri hendi
    elif topic == "0307VM":
        HondLeft.hreyfa_motor(int(skilabod))
        
    # Breyta lit á hægri auga
    elif topic == "0307HA":
        
        # Breyta augnarlit
        AugaH.breyta_lit(skilabod)
    
    
    elif topic == "0307VA":
        
        augaV.breyta_lit(skilabod)


# Tekur inn file og spilar það
# Verður að vera async
async def spila_hljod(file):
    
    await df.wait_available()
    await df.volume(15)
    await df.play(1, 1)
    await asyncio.sleep_ms(0)    



do_connect()



mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
mqtt_client.set_callback(fekk_skilabod)
mqtt_client.connect()

# Tengja við öll Topic
mqtt_client.subscribe(MAIN_TOPIC)
mqtt_client.subscribe(HM_TOPIC)
mqtt_client.subscribe(VM_TOPIC)
mqtt_client.subscribe(HA_TOPIC)
mqtt_client.subscribe(LA_TOPIC)


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
    


