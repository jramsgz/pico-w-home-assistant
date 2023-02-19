# Raspberry Pi Pico W MQTT devices for HomeAssistant

This repo contains the makerlab.mlha library and projects that make use of it.

## Library
makerlab.mlha is a client for HomeAssistant MQTT devices. It makes use of [umqtt.robust2](https://github.com/fizista/micropython-umqtt.robust2) to connect to a MQTT broker and then publishes its config and state to HomeAssistant. It also subscribes to the MQTT topics that HomeAssistant uses to control the device.

### Instructions
In order to use the library you need to have a MQTT broker running. I use [mosquitto](https://mosquitto.org/) but any other MQTT broker should work as well. You also need to have HomeAssistant running and configured to use the MQTT broker.

If you have everything set up, you just need to copy the library to your Pico W and import it in your project. The library is not yet available on PyPi so you need to copy it manually to your Pico W. You can do this by cloning the repo and then copying the library(/lib) folder to your Pico W. I personally use Thonny to copy the files to my Pico W.
Then you can import the library in your project. For example:
```python
from makerlab.mlha import MLHA 

mlha = MLHA(wifi_SSID, wifi_password, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
```

### Library usage
Here is a table with the available functions and their parameters.

| Function | Parameters | Description |
|----------|------------|-------------|
| `MLHA` | `wifi_SSID`, `wifi_password`, `mqtt_server`, `mqtt_port` (1883), `mqtt_user` (None), `mqtt_password` (None), `mqtt_keepalive` (1800) | Constructor. It connects to your WIFI, MQTT server and setups a watchdog to maintain the connection to the MQTT server |
| `set_callback` | `callback` | Sets the callback function that will be called when a MQTT message is received. The callback function must have the following signature: `callback(topic, message, retained, duplicate)` |
| `subscribe` | `topic`, `absolute` (False) | Subscribes to a MQTT topic. The topic must be a string. |
| `publish` | `topic`, `message`, `retain` (False) | Publishes a MQTT message to a topic. The topic must be a string. |
| `set_device_name` | `name` | Sets the name of the device. The name must be a string. |
| `set_enable_temp_sensor` | `enable` | Enables or disables the temperature sensor. |
| `update_temp_sensor` | None | Updates the temperature sensor. |
| `publish_config` | `discovery_topic`, `name`, `device_type` ("sensor"), `device_class` (None), `unit_of_measurement` (None), `state_class` (None), `state_topic` (""), `expire_after` (60) | Publishes the config for the device to HomeAssistant. Read HomeAssistant documentation for available options. |
| `publish_status` | `status` | Publishes the status all devices. The status must be a JSON object containing the discovery topic and the status. |
| `check_mqtt_msg` | None | Checks if there are any MQTT messages to process. This function must be called periodically. |

## Projects

Here is a list of my own projects that make use of the library.
Currently there are 2 projects, one for the climate control (reads temperatures and turns on/off the heater) and one for the alarm control (a simple button that can be used to arm and disarm the alarm system).

### Climate

The climate project is the way I control my heating system in my house. Schematics and code can be found in the projects/climate folder.
It consists of a Raspberry Pi Pico W (of course), x4 DS18B20 temperature sensors, a 8 channel relay board and a PIR module (the PIR is used as a part of the alarm system) which is synced and controlled via HomeAssistant using MQTT.

![Climate device in HomeAssistant](/projects/climate/screenshots/mqtt_ha.png)

### Alarm Control

The alarm control device is a simple button that can be used to arm and disarm the alarm system. It also has a LED that indicates the state of the alarm system. The code for this project can be found in the projects/alarm_control folder.
The alarm system I am using is just Home Assistant with Alarmo installed.

## Other Open Source projects

Take a look at [PicoW HomeAssistant Starter](https://github.com/daniloc/PicoW_HomeAssistant_Starter) by [daniloc](https://github.com/daniloc) for a similar functionality but made in C/C++. It is developed using a port of the RP2040 to the Arduino ecosystem which might produce a smaller binary size.
