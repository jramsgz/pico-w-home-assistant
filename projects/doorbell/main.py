import json
from secrets import wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password
from makerlab.mlha import MLHA 
from machine import Pin
import time
import gc

# Pins definition ===================================
button_pin = 14 # GPIO pin for the push button
relay_pin = 16 # GPIO pin for the bell relay

push_button = None  # Push button interrupt handler
bell_relay = None # Bell relay object
mlha = None # WiFi, MQTT and HomeAssistant library

# Functions =========================================
def parse_message(is_pressed=False):
    extracted_data = {"doorbell": is_pressed,
                      "mldoorbell_connection": True}

    return extracted_data


# Publishes the config for the sensors to Homeassistant
def setup_config():
    mlha.publish_config("doorbell", "Doorbell", "binary_sensor", "occupancy", expire_after = 140)
    mlha.publish_config("mldoorbell_connection", "MLDoorBell Connection", "binary_sensor", "connectivity", expire_after = 140)

def button_pressed(pin=None):
    if mlha is None:
        push_button.irq(trigger=Pin.IRQ_RISING, handler=None)
    if false_protection_check() == False:
        print("False press detected")
        return
    print("Bell is ringing")
    # Publish status
    if mlha is not None:
        mlha.publish_status(parse_message(True))
    # Start bell
    ring_bell()
    # Delay for 1 second
    time.sleep(1)
    # Stop bell
    bell_relay.value(0)
    if mlha is not None:
        mlha.publish_status(parse_message())
    else:
        push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

def ring_bell():
    for i in range(0, 7):
        bell_relay.value(1)
        time.sleep_ms(100 * i)
        bell_relay.value(0)
        time.sleep_ms(100 * i)

# False press check, check if the button is being pressed constantly for 0.150 seconds
def false_protection_check():
    start_time = time.ticks_ms()
    while (time.ticks_diff(time.ticks_ms(), start_time) < 150):
        if push_button.value() == 0:
            return False
    return True

# Main =============================================
# Initialise push button and its interrupt
print("Initializing push button")
push_button = Pin(button_pin, Pin.IN, Pin.PULL_DOWN)
push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# Initialise Relay
print("Initializing relay")
bell_relay = Pin(relay_pin, Pin.OUT)
bell_relay.value(0)

# Initialize main component (WiFi, MQTT and HomeAssistant)
mlha = MLHA(wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
mlha.set_device_name("MakerLab_Doorbell")
mlha.set_enable_temp_sensor(True)

print("Connected to MQTT broker")

# Publish config for sensors
print("Publishing config to Homeassistant")
setup_config()

print("Starting publish timer")
mlha.publish("system/status", "online", retain=True)
mlha.publish_status(parse_message())
print("Initialization complete, free memory: " + str(gc.mem_free()))
print("Ready to send/receive data")
# Disable interrupt
push_button.irq(trigger=Pin.IRQ_RISING, handler=None)

# Main loop
last_update = 0
while True:
    try:
        if time.ticks_diff(time.ticks_ms(), last_update) > 120000: # 2 minutes
            mlha.check_mqtt_msg()
            last_update = time.ticks_ms()
            mlha.publish_status(parse_message())
            mlha.update_temp_sensor()
        # Make sure relay is off
        if bell_relay.value() == 1:
            bell_relay.value(0)
        # Check if button is pressed
        if push_button.value() == 1:
            button_pressed()
    except Exception as ex:
        print("error: " + str(ex))
        machine.reset()
