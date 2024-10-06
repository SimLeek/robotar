"""Handling motors on Raspberry Pi GPIO pins"""
# todo: handle inputs as well
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)  # Using BCM numbering
# Setting up PWM pins
from typing import List, Tuple

def get_motor_handling(output_pins:List[Tuple[int,int]]):
    #PWM_PINS = [12, 13]  # Hardware PWM pins on Raspberry Pi 4
    #SW_PWM_PINS = [i for i in range(2, 28) if i not in PWM_PINS]  # All other pins for software PWM
    gpio_pins = []
    for output_pin in output_pins:
        gpio_pins.append(GPIO.PWM(output_pin[0], output_pin[1]))
        gpio_pins[-1].start(0)

    def motor_handling(tensor_buffer):
        pwms = tensor_buffer.tensors[0]
        for pin, pwm in enumerate(pwms):  # outermost dimension / rows=pins
            if pin<len(gpio_pins):
                gpio_pins[pin].ChangeDutyCycle(pwm * 100)

    return motor_handling
