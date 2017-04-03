#!/bin/bash
./build.sh
docker stop tellstick
docker rm tellstick

#     -v /srv/tellstick/data:/tellstick \

docker run -d --device=/dev/bus/usb --name tellstick \
	 adddrian/tellstick
