import i2c_driver
from threading import Timer
from datetime import datetime

TEMP_DEVICE_PATH='/sys/bus/w1/devices/28-011620e0f1ee/temperature'

to_deg_f = lambda celcius : celcius * 1.8 + 32

'''
The the kernel driver that reads from the DSB18B20 temperature probe,
outputs the temp as '24125'. Divide this by 1000 and you get 24.125, which
is in degrees celcius 

@return temparature in degrees celcius
'''
def getTemperature():
    temp = 0.0
    with open(TEMP_DEVICE_PATH) as f:
        data = f.read()
        temp = int(data.strip()) / 1000.0
    return temp

def displayTemperature(lcd, celcius, fahrenheit):
    now = datetime.now()
    time = now.strftime('%m/%d/%Y %H:%M:%S')
    lcd.lcd_display_string(time, 1)
    lcd.lcd_display_string("%.2f%s C / %.2f%s F" % (celcius, chr(223), fahrenheit, chr(223)), 2)

def update(lcd):
    celcius = getTemperature()
    fahrenheit = round(to_deg_f(celcius), 3)
    displayTemperature(lcd, celcius, fahrenheit)
    Timer(30.0, update, [lcd]).start()

my_lcd = i2c_driver.lcd()
my_lcd.lcd_clear()  
update(my_lcd)

