#!/bin/bash

/etc/init.d/telldusd start
echo "start callback"
python -u /tellstick/tellstickCallback.py --all
echo "callback exited"
while true
do
  echo "Press [CTRL+C] to stop.."
  sleep 100000
done
