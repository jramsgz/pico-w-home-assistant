# Raspberry Pi Pico W MQTT devices for HomeAssistant

> **Note**
> This is a work in progress. A documentation for the library will be added soon after I finish the first version of the library.

This repo contains the makerlab.mlha library and projects that make use of it.

## Library
makerlab.mlha is a client for HomeAssistant MQTT devices. It makes use of [umqtt.robust2](https://github.com/fizista/micropython-umqtt.robust2) to connect to a MQTT broker and then publishes its config and state to HomeAssistant. It also subscribes to the MQTT topics that HomeAssistant uses to control the device.

### Instructions
In order to use the library you need to have a MQTT broker running. I use [mosquitto](https://mosquitto.org/) but any other MQTT broker should work as well. You also need to have HomeAssistant running and configured to use the MQTT broker.

If you have everything set up, you just need to copy the library to your Pico W and import it in your project. The library is not yet available on PyPi so you need to copy it manually to your Pico W. You can do this by cloning the repo and then copying the library(/lib) folder to your Pico W. I personally use Thonny to copy the files to my Pico W.
Then you can import the library in your project. For example:
```python
import makerlab.mlha as mlha
```
Instructions on how to use the library will be added soon.

## Projects

### Climate

The climate project is the way I control my heating system in my house. Schematics and code can be found in the projects/climate folder.
It consists of a Raspberry Pi Pico W (of course), x4 DS18B20 temperature sensors, a 8 channel relay board and a PIR module (the PIR is used as a part of the alarm system) which is synced and controlled via HomeAssistant using MQTT.

*Note: This is a temporary placeholder screenshot. Needs replacement*
![Climate device in HomeAssistant](/projects/climate/screenshots/mqtt_ha.png)

### Alarm Control

The alarm control device is a simple button that can be used to arm and disarm the alarm system. It also has a LED that indicates the state of the alarm system. The code for this project can be found in the projects/alarm_control folder.
