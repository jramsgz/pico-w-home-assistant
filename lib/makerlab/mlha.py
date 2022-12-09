#
# Custom library made to reuse code for all my devices that connect to Home Assistant
#
# This library doest the following:
#
# 1. Connect to a WiFi network
# 2. Connect to an MQTT broker
# 3. Send configuration data to the broker for home assistant
# 4. Subscribe to topics
# 5. Publish data to the broker
#
#   -- Jesús Ramos, 30-Nov-2022
#

import json
import ubinascii
import network
from umqtt.robust2 import MQTTClient
import machine
from machine import Timer, Pin
import time

class MLHA:
    def __init__(self, wifi_ssid, wifi_password, mqtt_server, mqtt_port=1883, mqtt_user=None, mqtt_password=None, mqtt_keepalive=1800):
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_keepalive = mqtt_keepalive
        
        self.pico_id = "pico-" + ubinascii.hexlify(machine.unique_id()).decode()
        self.led = Pin("LED", Pin.OUT)
        self.wlan = network.WLAN(network.STA_IF)
        self.mqtt = MQTTClient(self.pico_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password, keepalive=mqtt_keepalive)

        self.mqtt_callback = None
        self.error_count = 0 # Used to keep track of the number of errors in case of a network failure
        # While the following bug is being worked on https://github.com/micropython/micropython/issues/9505, error_count is used to work around the issue

        # Start Initialization
        print(self.pico_id)
        print("ML HA v0.1")

        # Check if LED works
        print("Checking LED for 5 seconds")
        self.led.on()
        time.sleep(5)

        # Initialise Wifi
        print("Initializing WiFi")
        self.connectWifi()

        # Initialise MQTT
        print("Initializing MQTT")
        self.connectMQTT()

        # Start connection watchdog
        print("Starting watchdog")
        self.watchdog = Timer()
        self.watchdog.init(period=2500, mode=Timer.PERIODIC, callback=self.watchdog_cb)
        print("ML HA Initialized")
    
    def toggle_led(self, t):
        self.led.toggle()

    def connectWifi(self):
        # STA_IF = station interface, AP_IF = Access Point interface
        self.wlan.active(True)
        self.wlan.connect(self.wifi_ssid, self.wifi_password)

        # Wait for connect, fail after 30 seconds
        max_wait = 30
        # Checking Wi-Fi before continuing
        tim = Timer()
        tim.init(freq=3, mode=Timer.PERIODIC, callback=self.toggle_led)
        while self.wlan.status() != 3:
            print("Waiting, wlan status " + str(self.wlan.status()))
            max_wait -= 1
            if max_wait == 0:
                print("Failed to connect to WiFi")
                machine.reset()
            time.sleep(1)
        print("Connected, wlan status " + str(self.wlan.status()))
        status = self.wlan.ifconfig()
        print('connected as ' + status[0])
        tim.deinit()
        self.led.off()

    def watchdog_cb(self, t):
        # If there is a connection issue for 10 seconds, we reset the Pico
        if self.error_count > 10:
            print("MQTT connection lost, resetting")
            machine.reset()
        if self.mqtt.is_conn_issue():
            print("MQTT connection issue, count: " + str(self.error_count))
            self.error_count += 1
            self.mqtt.disconnect()
            self.mqtt.reconnect()
            self.mqtt.resubscribe()
        else:
            self.error_count = 0

    def connectMQTT(self):
        self.mqtt.set_last_will(self.pico_id + "/system/status", "offline", retain=True)
        self.mqtt.connect()
        # Print diagnostic messages when retries/reconnects happens
        self.mqtt.DEBUG = True
        # Information whether we store unsent messages with the flag QoS==0 in the queue.
        self.mqtt.KEEP_QOS0 = False
        # Option, limits the possibility of only one unique message being queued.
        self.mqtt.NO_QUEUE_DUPS = True
        # Limit the number of unsent messages in the queue.
        self.mqtt.MSG_QUEUE_MAX = 2
        # Sets the callback function for the MQTTClient object.
        self.mqtt.set_callback(self.sub_cb)

    def sub_cb(self, topic, msg, retained, duplicate):
        self.led.on()
        print("Received message on topic " + (topic).decode() + "( " + str(retained) + "|" + str(duplicate) + " )" + ": " + (msg).decode())
        if self.mqtt_callback is not None:
            self.mqtt_callback((topic).decode().replace(self.pico_id+"/", ''), msg, retained, duplicate)
        self.led.off()
    
    def set_callback(self, callback):
        self.mqtt_callback = callback
    
    def subscribe(self, topic, absolute=False):
        if absolute:
            self.mqtt.subscribe(topic)
        else:
            self.mqtt.subscribe(self.pico_id + "/" + topic)

    def publish(self, topic, msg, retain=False):
        self.mqtt.publish(b""+self.pico_id + "/" + topic, msg, retain)

    # Discovery packet for Homeassistant
    def publish_config(self, discovery_topic, name, device_type="sensor", device_class=None, unit_of_measurement=None, state_class=None):
        print("Publishing discovery packet for " + name)
        config_payload = {
            "name": name,
            "state_topic": self.pico_id + "/state",
            "availability": [
                {
                    "topic": self.pico_id + "/system/status",
                    "payload_available": "online",
                    "payload_not_available": "offline"
                }
            ],
            "device": {
                "identifiers": self.pico_id,
                "name": "MLCasaTemp",
                "manufacturer": "MakerLab",
                "model": "RPI Pico W MLHA",
                "sw_version": "0.1",
                "connections": [ ["ip", self.wlan.ifconfig()[0]], ["mac", ubinascii.hexlify(self.wlan.config('mac')).decode()] ]
            },
            "unique_id": self.pico_id + "-" + discovery_topic,
            "device_class": device_class,
            "value_template": "{{ value_json." + discovery_topic + " }}",
            "unit_of_measurement": unit_of_measurement,
            "state_class": state_class,
            "expire_after": 60
        }

        if device_class is None:
            del config_payload["device_class"]
        if unit_of_measurement is None:
            del config_payload["unit_of_measurement"]
        if state_class is None:
            del config_payload["state_class"]

        if device_type == "binary_sensor":
            config_payload["payload_on"] = True
            config_payload["payload_off"] = False
            if device_class is "connectivity":
                config_payload["entity_category"] = "diagnostic"

        if device_type == "switch":
            config_payload["command_topic"] = self.pico_id + "/switch/toggle/" + discovery_topic
            config_payload["payload_on"] = True
            config_payload["payload_off"] = False
            config_payload["state_on"] = True
            config_payload["state_off"] = False
            config_payload["icon"] = "mdi:power"

        self.mqtt.publish("homeassistant/" + device_type + "/" + self.pico_id + "/" + discovery_topic + "/config", json.dumps(config_payload), retain=True)

    def publish_status(self, status_data):
        self.led.on()
        if not self.mqtt.is_keepalive():
            # Dont do anything if we are not connected
            print("MQTT not connected, skipping")
            return
        stringified_data = json.dumps(status_data)
        self.mqtt.publish(self.pico_id + "/system/status", "online", retain=True)
        self.mqtt.publish(self.pico_id + "/state", stringified_data)
        self.led.off()

    def check_mqtt_msg(self):
        try:
            # Do nothing if the connection is not established, the timer will handle reconnection
            if self.mqtt.is_keepalive():
                self.mqtt.check_msg() # needed when publish(qos=1), ping(), subscribe()
                self.mqtt.send_queue() # needed when using the caching capabilities for unsent messages
        except Exception as ex:
            print("error: " + str(ex))
            machine.reset()
