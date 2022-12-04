# Raspberry Pi Pico W MQTT devices for HomeAssistant

Note: This is a work in progress. A documentation for the library will be added soon after I finish the first version of the library.

This is a collection of devices for HomeAssistant that use the Raspberry Pi Pico W to monitor and control things around the house.

## Devices

### Climate

The climate device is a simple thermostat that uses some DS18B20 temperature sensors to monitor the temperature and relays to control the heating system of my house.
Everything is monitored and controlled via HomeAssistant using MQTT.
