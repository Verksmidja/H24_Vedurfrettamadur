from machine import Pin, ADC
import uasyncio as asyncio
from lib.dfplayer import DFPlayer
from servo import Servo

df = DFPlayer(2)  # using UART
df.init(tx=17, rx=16)  # tx on ESP connects to rx on MP3

adc14 = ADC(Pin(14))

servo = Servo(Pin(12))

min_angle = 53
max_angle = 135
closed_angle = min_angle  

async def play_audio():
    await df.wait_available() 
    await df.volume(30)
    await df.play(2, 1)  
    print("Audio playing...")

async def read_analog():
    while True:
        val14 = adc14.read()
        
        if val14 < 150:
            angle = closed_angle
        else:
            angle = min_angle + int(((val14 - 190) / (1000 - 190)) * (max_angle - min_angle))
        
        servo.write_angle(angle)
        
        print(f"Analog: {val14}, Angle: {angle}")
        
        await asyncio.sleep(0.1)  

async def main():
    await play_audio()
    await read_analog()  

asyncio.run(main())
