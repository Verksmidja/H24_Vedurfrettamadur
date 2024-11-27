import machine
import dht
import time

dht22 = dht.DHT22(machine.Pin(10))

while True:
    try:
        # Trigger measurement
        dht22.measure()
        temperature = dht22.temperature()  # In Celsius
        humidity = dht22.humidity()       # Relative humidity

        # Print the values
        print("Temperature: {:.1f}°C".format(temperature))
        print("Humidity: {:.1f}%".format(humidity))

    except OSError as e:
        print("Failed to read sensor data:", e)
    
    time.sleep(2)  # Wait 2 seconds before reading again. You need a little wait for stable readings