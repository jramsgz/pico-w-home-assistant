#
# Project to read temperature from some DS18B20 sensors and publish them to MQTT
# Then Home Assistant can read the temperature from MQTT and use it as a climate
# entity to control the heating system using relays connected to the Pico.
#
# In brief, this project:
#
# 1. Loads the secrets from the secrets.py file and loads the common MLHA library
# in order to connect to WiFi, MQTT and Home Assistant.
# 2. Sets up the DS18B20 sensors and the relays to control the heating system.
# 5. Sets up the MQTT publishing of the configuration of the sensors to Home Assistant.
# 3. Sets up the MQTT subscriptions to receive commands from Home Assistant.
# 4. Sets up the MQTT publishing of the temperature and the status of the relays.
# 6. Sets up a timer to read the temperature from the sensors and publish it to MQTT.
#

import json
from secrets import wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password
from makerlab.mlha import MLHA 
from machine import Pin
import onewire, ds18x20
import time
import gc

# Pins definition ===================================
ds_caldera_pin = 26 # GPIO pin for caldera temperature data
ds_deposito_pin = 22 # GPIO pin for deposito temperature data
ds_casa_pin = 21 # GPIO pin for casa temperature data
ds_exterior_pin = 20 # GPIO pin for exterior temperature data
relay_caldera_pin = 13 # GPIO pin for caldera relay
relay_acs_pin = 9 # GPIO pin for ACS relay
relay_primerod_pin = 10 # GPIO pin for primerod relay
relay_garaje_pin = 14 # GPIO pin for garaje relay
relay_gen1_pin = 15 # GPIO pin for relay
relay_gen2_pin = 12 # GPIO pin for relay
relay_gen3_pin = 11 # GPIO pin for relay
relay_gen4_pin = 8 # GPIO pin for relay
pir_pin = 18 # GPIO pin for the PIR sensor

ds_caldera_sensor = None  # caldera temperature sensor object (Dallas)
ds_deposito_sensor = None # depositotemperature sensor object (Dallas)
ds_casa_sensor = None  # casa temperature sensor object (Dallas)
ds_exterior_sensor = None # exterior temperature sensor object (Dallas)
relay_caldera = None # relay for caldera
relay_acs = None # relay for acs
relay_primerod = None # relay for primerod
relay_garaje = None # relay for garaje
relay_gen1 = None # relay
relay_gen2 = None # relay
relay_gen3 = None # relay
relay_gen4 = None # relay
temperatura_caldera = None # temperatura caldera
temperatura_deposito = None # temperatura deposito
temperatura_casa = None # temperatura casa
temperatura_exterior = None # temperatura exterior
pir_sensor = None # PIR sensor object
mlha = None # WiFi, MQTT and HomeAssistant library

# Functions =========================================
def getTemperature():
    global temperatura_caldera
    global temperatura_deposito
    global temperatura_casa
    global temperatura_exterior
    try:
        caldera_sensor_id = ds_caldera_sensor.scan()[0]
        ds_caldera_sensor.convert_temp()
        temperatura_caldera = ds_caldera_sensor.read_temp(caldera_sensor_id)
    except Exception as e:
        print("Error getting caldera temperature: " + str(e))
    try:
        deposito_sensor_id = ds_deposito_sensor.scan()[0]
        ds_deposito_sensor.convert_temp()
        temperatura_deposito = ds_deposito_sensor.read_temp(deposito_sensor_id)
    except Exception as e:
        print("Error getting deposito temperature: " + str(e))
    try:
        casa_sensor_id = ds_casa_sensor.scan()[0]
        ds_casa_sensor.convert_temp()
        temperatura_casa = ds_casa_sensor.read_temp(casa_sensor_id)
    except Exception as e:
        print("Error getting casa temperature: " + str(e))
    try:
        exterior_sensor_id = ds_exterior_sensor.scan()[0]
        ds_exterior_sensor.convert_temp()
        temperatura_exterior = ds_exterior_sensor.read_temp(exterior_sensor_id)
    except Exception as e:
        print("Error getting exterior temperature: " + str(e))
    
    # Check temperature values are valid
    if temperatura_caldera < 0 or temperatura_caldera > 84:
        temperatura_caldera = None
    if temperatura_deposito < 0 or temperatura_deposito > 84:
        temperatura_deposito = None
    if temperatura_casa < 0 or temperatura_casa > 50:
        temperatura_casa = None
    if temperatura_exterior < -20 or temperatura_exterior > 60:
        temperatura_exterior = None

def msg_received(topic, msg, retained, duplicate):
    if topic == "system/status":
        mlha.publish("system/status", "online")
    elif topic == "switch/toggle/caldera_status":
        if msg == b"True":
            relay_caldera.value(0)
        elif msg == b"False":
            relay_caldera.value(1)
    elif topic == "switch/toggle/acs_status":
        if msg == b"True":
            relay_acs.value(0)
        elif msg == b"False":
            relay_acs.value(1)
    elif topic == "switch/toggle/primerod_status":
        if msg == b"True":
            relay_primerod.value(0)
        elif msg == b"False":
            relay_primerod.value(1)
    elif topic == "switch/toggle/garaje_status":
        if msg == b"True":
            relay_garaje.value(0)
        elif msg == b"False":
            relay_garaje.value(1)
    elif topic == "switch/toggle/gen1_status":
        if msg == b"True":
            relay_gen1.value(0)
        elif msg == b"False":
            relay_gen1.value(1)
    elif topic == "switch/toggle/gen2_status":
        if msg == b"True":
            relay_gen2.value(0)
        elif msg == b"False":
            relay_gen2.value(1)
    elif topic == "switch/toggle/gen3_status":
        if msg == b"True":
            relay_gen3.value(0)
        elif msg == b"False":
            relay_gen3.value(1)
    elif topic == "switch/toggle/gen4_status":
        if msg == b"True":
            relay_gen4.value(0)
        elif msg == b"False":
            relay_gen4.value(1)
    else:
        print("Unknown topic")
    mlha.publish_status(parse_message())

def parse_message():
    extracted_data = {"caldera_temp": temperatura_caldera,
                      "casa_temp": temperatura_casa,
                      "exterior_temp": temperatura_exterior,
                      "deposito_temp": temperatura_deposito,
                      "caldera_status": relay_caldera.value() == 0,
                      "acs_status": relay_acs.value() == 0,
                      "primerod_status": relay_primerod.value() == 0,
                      "garaje_status": relay_garaje.value() == 0,
                      "gen1_status": relay_gen1.value() == 0,
                      "gen2_status": relay_gen2.value() == 0,
                      "gen3_status": relay_gen3.value() == 0,
                      "gen4_status": relay_gen4.value() == 0,
                      "mltemp_connection": True}

    return extracted_data


def read_and_publish():
    getTemperature()
    mlha.publish_status(parse_message())

# Publishes the config for the sensors to Homeassistant
def setup_config():
    mlha.publish_config("caldera_temp", "Temperatura de la Caldera", "sensor", "temperature", None, "measurement", expire_after = 60)
    mlha.publish_config("casa_temp", "Temperatura de Casa", "sensor", "temperature", None, "measurement", expire_after = 60)
    mlha.publish_config("exterior_temp", "Temperatura Exterior", "sensor", "temperature", None, "measurement", expire_after = 60)
    mlha.publish_config("deposito_temp", "Temperatura del Deposito", "sensor", "temperature", None, "measurement", expire_after = 60)
    mlha.publish_config("caldera_status", "Estado de la caldera", "switch", expire_after = 60)
    mlha.publish_config("acs_status", "Estado del ACS", "switch", expire_after = 60)
    mlha.publish_config("primerod_status", "Estado del Primero D", "switch", expire_after = 60)
    mlha.publish_config("garaje_status", "Estado del Garaje", "switch", expire_after = 60)
    mlha.publish_config("cuadra_motion", "Movimiento en la cuadra", "binary_sensor", "motion", state_topic = "/motion", expire_after = 60)
    mlha.publish_config("mltemp_connection", "MLTemp Connection", "binary_sensor", "connectivity", expire_after = 60)
    mlha.publish_config("gen1_status", "Estado del rele gen 1", "switch", expire_after = 60)
    mlha.publish_config("gen2_status", "Estado del rele gen 2", "switch", expire_after = 60)
    mlha.publish_config("gen3_status", "Estado del rele gen 3", "switch", expire_after = 60)
    mlha.publish_config("gen4_status", "Estado del rele gen 4", "switch", expire_after = 60)

# Main =============================================
# Initialize main component (WiFi, MQTT and HomeAssistant)
mlha = MLHA(wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
mlha.set_callback(msg_received)
mlha.set_device_name("MLCasaClimate")

# Initialise temperature sensors
print("Initializing temperature sensors")
ds_caldera_sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(ds_caldera_pin)))
ds_deposito_sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(ds_deposito_pin)))
ds_casa_sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(ds_casa_pin)))
ds_exterior_sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(ds_exterior_pin)))

# Initialise Relays
print("Initializing relays")
relay_caldera = Pin(relay_caldera_pin, Pin.OUT)
relay_acs = Pin(relay_acs_pin, Pin.OUT)
relay_primerod = Pin(relay_primerod_pin, Pin.OUT)
relay_garaje = Pin(relay_garaje_pin, Pin.OUT)
relay_gen1 = Pin(relay_gen1_pin, Pin.OUT)
relay_gen2 = Pin(relay_gen2_pin, Pin.OUT)
relay_gen3 = Pin(relay_gen3_pin, Pin.OUT)
relay_gen4 = Pin(relay_gen4_pin, Pin.OUT)
relay_caldera.value(1)
relay_acs.value(1)
relay_primerod.value(1)
relay_garaje.value(1)
relay_gen1.value(1)
relay_gen2.value(1)
relay_gen3.value(1)
relay_gen4.value(1)

# Initialize PIR sensor
print("Initializing PIR sensor")
pir_sensor = Pin(pir_pin, Pin.IN)

# Subscribe to topics
print("New session being set up")
mlha.subscribe("switch/toggle/caldera_status")
mlha.subscribe("switch/toggle/acs_status")
mlha.subscribe("switch/toggle/primerod_status")
mlha.subscribe("switch/toggle/garaje_status")
mlha.subscribe("switch/toggle/gen1_status")
mlha.subscribe("switch/toggle/gen2_status")
mlha.subscribe("switch/toggle/gen3_status")
mlha.subscribe("switch/toggle/gen4_status")
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
last_pir_value = 2 # Force first check and publish
while True:
    try:
        mlha.check_mqtt_msg()
        # Check PIR sensor
        if pir_sensor.value() != last_pir_value or time.ticks_diff(time.ticks_ms(), last_update) > 30000:
            last_pir_value = pir_sensor.value()
            if last_pir_value == 1:
                print("Motion detected")
                mlha.publish("motion/state", "True")
            else:
                print("Motion stopped")
                mlha.publish("motion/state", "False")
        # Send data to broker every 30 seconds
        if time.ticks_diff(time.ticks_ms(), last_update) > 30000: # 30 seconds
            last_update = time.ticks_ms()
            read_and_publish()
        time.sleep_ms(250)
    except Exception as ex:
        print("error: " + str(ex))
        machine.reset()
