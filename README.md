# Tellstick Duo Mqtt docker build

### Concept
This service will work as a gateway between the tellstick duo and a mqtt broker.

#### The service can:
* Send sensordata from the tellstick to mqtt messages
* Change state (turn on/off) a device on an mqtt trigger

#### Mqtt structure:
##### sensordata
```
sensors/<room>/<sensor type>/<sensor id>/sensors
```
###### Example
```
sensors/living_room/humidity/135/sensors
```
##### Trigger message'
```
devices/tellstick/<room>/<description>
```
###### Example
```
devices/tellstick/bedroom/desk_lamp
```
### Deploy

#### Building from source

```sh
cd <git root>/build
docker build -t adddrian/tellstick .
```


#### Run it as a logger (will only print all messages it recivies in the log)

```sh
docker run -d --device=/dev/bus/usb --name tellstick adddrian/tellstick
docker build -t adddrian/tellstick build/.
docker logs tellstick
```
##### Example log of tellstick:
[SENSOR] 191 [fineoffset/temperature] (1) @ 1491300564 <- 9.6
[RAW] 1 <- class:sensor;protocol:fineoffset;id:183;model:temperaturehumidity;humidity:35;temp:22.9;
[RAW] 1 <- class:sensor;protocol:fineoffset;id:135;model:temperaturehumidity;humidity:29;temp:22.6;
[RAW] 1 <- class:sensor;protocol:fineoffset;id:136;model:temperature;temp:8.6;
[RAW] 1 <- class:sensor;protocol:fineoffset;id:183;model:temperaturehumidity;humidity:35;temp:22.9;
[RAW] 1 <- class:sensor;protocol:fineoffset;id:135;model:temperaturehumidity;humidity:29;temp:22.6;
[RAW] 1 <- class:sensor;protocol:fineoffset;id:136;model:temperature;temp:8.6;

#### Run it persistent
```sh
docker run -d --device=/dev/bus/usb --name tellstick \
  -v /srv/tellstick/tellstick.conf:/etc/tellstick.conf \
  -v /srv/tellstick/config.yaml:/tellstick/config.yaml \
adddrian/tellstick
```

Reuse tellstick config 
```sh
mv /etc/tellstick.conf /srv/tellstick/tellstick.conf
```

config
----

Mqtt settings (Required)
```yml
mqtt: 
  host: mqtt.example.org
  port: 1883
  authentication:
    username: test
    password: test2
```

Sensors to send to Mqtt (Optional)
```yml
sensor: 
  - id: 183
    protocol: fineoffset
    model: temperaturehumidity
    dataType: 1
    mqttRoom: bedroom
    mqttSensorType: temperature

  - id: 183
    protocol: fineoffset
    model: temperaturehumidity
    dataType: 2
    mqttRoom: bedroom
    mqttSensorType: humidity
```
Raw message to send to Mqtt (Optional)
```yml
raw:
  - tellstickMessage: class:command;protocol:arctech;model:selflearning;house:15139302;unit:10;group:0;method:turnon;
    mqttRoom: hall
    mqttSensorType: motion
    mqttDescription: 15139302
    mqttPayload: 1
```

Switch mqtt listener (Optional)
```yml
switch: 
  - mqttRoom: livingroom
    mqttDescription: tv_lamp
tellstickDeviceId: 2
```

License
----
GNU General Public License v3.0
