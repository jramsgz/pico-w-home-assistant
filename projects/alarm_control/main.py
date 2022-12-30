#
# Project to activate a script in Home Assistant when pressing a button, it is published via MQTT
# Then Home Assistant can read the event and activate the script
# It is used to temporarily deactivate the alarm system, it therefore needs to read the status of the alarm system
#
# In brief, this project:
#
# 1. Loads the secrets from the secrets.py file and loads the common MLHA library
# in order to connect to WiFi, MQTT and Home Assistant.
# 2. Sets up the button and the LEDs
# 5. Sets up the MQTT publishing of the configuration of the sensors to Home Assistant.
# 3. Sets up the MQTT subscriptions to receive commands from Home Assistant.
# 4. Sets up the MQTT publishing of the button state to Home Assistant.
# 6. Sets up a timer to read the button state and publish it to MQTT.
#
# Notes on changing the code:
# - When the program is running, the on-board LED of the Pico board is lit. If 
#   you are using a UI like the recommended Thonny, you can simply halt the 
#   program when LED is on and update the program.
#
#     -- Jesús Ramos, 04-Dec-2022
#

import json
from secrets import wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password
from makerlab.mlha import MLHA 
from machine import Pin, Timer
import time
import gc

# Pins definition ===================================
button_pin = 12 # GPIO pin for the push button
red_led_pin = 11 # GPIO pin for the red LED
green_led_pin = 10 # GPIO pin for the green LED

push_button = None  # Push button interrupt handler
red_led = None # Red LED object
green_led = None  # Green LED object
alarm_active = False # Alarm status
mlha = None # WiFi, MQTT and HomeAssistant library

# Functions =========================================
def msg_received(topic, msg, retained, duplicate):
    if topic == "system/status":
        mlha.publish("system/status", "online")
    elif topic == "alarmo/interior/state":
        global alarm_active
        alarm_active = msg == b"armed_home" or msg == b"armed_away" or msg == b"armed_night"
        print("Alarm status: " + str(alarm_active))
        red_led.value(alarm_active)
        green_led.value(not alarm_active)
    else:
        print("Unknown topic")
    extracted_data = parse_message()
    stringified_data = json.dumps(extracted_data)
    mlha.publish("state", stringified_data)

def parse_message(is_pressed=False):
    extracted_data = {"activator": is_pressed,
                      "mlactivator_connection": True}

    return extracted_data


# Publishes the config for the sensors to Homeassistant
def setup_config():
    mlha.publish_config("activator", "Activador simple", "binary_sensor", "running", expire_after = 140)
    mlha.publish_config("mlactivator_connection", "MLActivator Connection", "binary_sensor", "connectivity", expire_after = 140)

def button_pressed(pin):
    push_button.irq(trigger=Pin.IRQ_RISING, handler=None)
    print("Button pressed")
    mlha.publish_status(parse_message(True))
    time.sleep(2)
    mlha.publish_status(parse_message())
    push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)
    

# Main =============================================
# Initialize main component (WiFi, MQTT and HomeAssistant)
mlha = MLHA(wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
mlha.set_callback(msg_received)
mlha.set_device_name("MLCasaAlarmControl")
mlha.set_enable_temp_sensor(True)

# Initialise push button and its interrupt
print("Initializing push button")
push_button = Pin(button_pin, Pin.IN, Pin.PULL_DOWN)
push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# Initialise LEDs
print("Initializing LEDs")
red_led = Pin(red_led_pin, Pin.OUT)
green_led = Pin(green_led_pin, Pin.OUT)

# Subscribe to topics
print("New session being set up")
mlha.subscribe("switch/toggle/activator")
mlha.subscribe("alarmo/interior/state", True)
print("Connected to MQTT broker and subscribed to topics")

# Publish config for sensors
print("Publishing config to Homeassistant")
setup_config() # Publishes the config for Homeassistant

print("Starting values read and publish timer")
# Send ping to broker every 2 minutes
send_tim = Timer()
send_tim.init(period=120000, mode=Timer.PERIODIC, callback=lambda t:mlha.publish_status(parse_message()))
mlha.publish_status(parse_message())
print("Initialization complete, free memory: " + str(gc.mem_free()))
print("Ready to send/receive data")
mlha.publish("system/status", "online", retain=True)

# Main loop
last_update = time.ticks_ms()
while True:
    try:
        mlha.check_mqtt_msg()
        if time.ticks_diff(time.ticks_ms(), last_update) > 120000: # 2 minutes
            last_update = time.ticks_ms()
            mlha.update_temp_sensor()
        time.sleep_ms(250)
    except Exception as ex:
        print("error: " + str(ex))
        machine.reset()
