# Tellstick_Mqtt_docker_build
Tellstick duo Mqtt docker service

#### This is an example message intercepted from a Proove Temperature Humidity sensor
##### class:sensor;protocol:fineoffset;data:4B70E41A22; 
The id of the sensor is 183, the temperature is 22.8 degrees Celsius and the Relative humidity is 26%RH
Printing the data portion of the message as binary results in the following bits where "dc" represents don't care about these bits":

| dc | id | dc | 22.8°C | 26%RH | dc |
| -- | -- | -- | ------ | ----- | ---|
0100 | 10110111 | 0000 | 11100100 | 00011010 | 0010 0010 |
