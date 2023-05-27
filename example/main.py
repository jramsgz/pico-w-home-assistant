from secrets import wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password
from makerlab.mlha import MLHA 
from machine import Pin
import time
import gc

# Pins definition ===================================
button_pin = 15 # GPIO pin for the push button
led_pin = 16 # GPIO pin for the led

button = None  # Button object
led = None # Led object
mlha = None # WiFi, MQTT and HomeAssistant library

# Functions =========================================
def msg_received(topic, msg, retained, duplicate):
    if topic == "system/status":
        mlha.publish("system/status", "online")
    elif topic == "switch/toggle/led":
        if msg == b"True":
            led.value(1)
        elif msg == b"False":
            led.value(0)
    else:
        print("Unknown topic")
    mlha.publish_status(parse_message())

def parse_message():
    extracted_data = {"led": led.value() == 1,
                      "example_connection": True}

    return extracted_data

def button_pressed(pin):
    # Disable interrupt to avoid multiple presses
    push_button.irq(trigger=Pin.IRQ_RISING, handler=None)
    print("Button pressed")
    if led.value() == 0:
        led.value(1)
    else:
        led.value(0)
    read_and_publish()
    time.sleep_ms(500)
    push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

def read_and_publish():
    mlha.publish_status(parse_message())

# Publishes the config for the sensors to Homeassistant
def setup_config():
    mlha.publish_config("led", "Led", "binary_sensor", expire_after = 60)
    mlha.publish_config("example_connection", "Example Connection", "binary_sensor", "connectivity", expire_after = 60)

# Main =============================================
# Initialize main component (WiFi, MQTT and HomeAssistant)
mlha = MLHA(wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
mlha.set_callback(msg_received)
mlha.set_device_name("ExampleMLHA")
mlha.set_enable_temp_sensor(True)

# Initialize led
print("Initializing led")
relay_caldera = Pin(led_pin, Pin.OUT)

# Initialise push button and its interrupt
print("Initializing push button")
push_button = Pin(button_pin, Pin.IN, Pin.PULL_DOWN)
push_button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# Subscribe to topics
print("New session being set up")
mlha.subscribe("switch/toggle/led")
print("Connected to MQTT broker and subscribed to topics")

# Publish config for sensors
print("Publishing config to Homeassistant")
setup_config() # Publishes the config for Homeassistant

print("Starting values read and publish timer")
print("Initialization complete, free memory: " + str(gc.mem_free()))
print("Ready to send/receive data")
mlha.publish("system/status", "online", retain=True)

# Main loop
last_update = 0
while True:
    try:
        mlha.check_mqtt_msg()
        # Send data to broker every 30 seconds
        if time.ticks_diff(time.ticks_ms(), last_update) > 30000: # 30 seconds
            last_update = time.ticks_ms()
            read_and_publish()
            mlha.update_temp_sensor()
        time.sleep_ms(250)
    except Exception as ex:
        print("error: " + str(ex))
        machine.reset()
