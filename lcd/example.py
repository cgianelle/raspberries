import i2c_driver

my_lcd = i2c_driver.lcd()

my_lcd.lcd_clear()

my_lcd.lcd_display_string("hello world", 1)
my_lcd.lcd_display_string("hello world", 2)
my_lcd.lcd_display_string("hello world", 3)
my_lcd.lcd_display_string("hello world", 4)