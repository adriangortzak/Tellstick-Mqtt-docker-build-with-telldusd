#!/bin/bash
./build.sh
docker stop tellstick
docker rm tellstick

docker run -d --device=/dev/bus/usb --name tellstick \
  -v /srv/tellstick/tellstick.conf:/etc/tellstick.conf \
  -v /srv/tellstick/config.yaml:/tellstick/config.yaml \
	 adddrian/tellstick
