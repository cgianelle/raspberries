'''
Digital Pulse Width Modulation, or PWM, is a digital on/off
signal that pulses up and down at various frequency rates and duty cycles.
The frequency rate is a measure of how often the pulse repeats
and is generally expressed as "hertz" or cycles per second.

The higher the duty cycle, the higher the average voltage applied
to the DC motor, resulting in an increase in motor speed. The shorter
the duty cycle, the lower the average voltage applied to the DC
motor, resulting in a decrease in motor speed.

duty cycle is the time in which the signal is on. the higher the
value, the longer that signal is "on" and the lower the value the longer
that signal is off.

The frequency is just how often that cycle repeats.
'''
from machine import Pin, PWM
in1A = Pin(1, Pin.OUT)
in2A = Pin(2, Pin.OUT)

in1B = Pin(14, Pin.OUT)
in2B = Pin(15, Pin.OUT)

enA = PWM(Pin(0, Pin.OUT))
enB = PWM(Pin(13, Pin.OUT))

def setPitchingDirection():
    in1A.high()
    in2A.low()

    in1B.low()
    in2B.high()

def setPitchFrequency(frequency):
    enA.freq(frequency)
    enB.freq(frequency)

def setPitchingDuty(a_speed, b_speed):
    enA.duty_u16(a_speed)
    enB.duty_u16(b_speed)

def stopPitching():
    setPitchingDuty(0,0)
    
def setFastball(speed):
    setPitchingDuty(speed, speed)
    
