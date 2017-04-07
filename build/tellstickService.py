
import argparse
import sys
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import re
import threading
from collections import namedtuple
import ruamel.yaml as yaml

import time
import datetime
from pylibftdi import USB_PID_LIST, USB_VID_LIST, Device as TellStick
from rf433.Protocol import Protocol, Device
from Queue import *

USB_PID_LIST.append(0x0c31)
USB_VID_LIST.append(0x1781)

q = Queue()

baudrate=9600
mydevice = None
tellstick = TellStick(mode='t')
tellstick.flush()
target = []
shared_dict = {}
lock = threading.Lock()

try:
  configpath = sys.argv[1]
except:
  print "Usage: tellstickService.py <path to config directory>"
  sys.exit(1)

def reader():
    while True:
        data = tellstick.read(1024)
        if data != '':
          parseReading(data)
          

def writer():
    while True:
        item = q.get()
        if item is None:
            break
        protocol = item[0]
        model = item[1]
        house = item[2]
        unit = item[3]
        command = item[4]
        msg = ""
        
        myDevice = Protocol.protocolInstance(protocol)
        myDevice.setModel(model)
        myDevice.setParameters({'house': house, 'unit': unit})
        
        if command == "0":
          msg = myDevice.stringForMethod(Device.TURNOFF, 0)
        elif command == "1":
          msg = myDevice.stringForMethod(Device.TURNON, 0)
        if 'S' in msg:
          toSend = 'S%s+' % msg['S']
          for x in range(1,2):
            tellstick.write(toSend)
            time.sleep(1) # Make sure you sleep or else it won't like getting another command so soon! Was 2 seconds before
        else:
            print "nothing to send"
            time.sleep(0.1)

def parseReading(msg):
    mswitch = re.search(r"protocol:([a-z]+);model:([a-z]+);data:(.+);", msg)
    msensor = re.search(r"class:sensor;protocol:([a-z]+);data:(.+);", msg)
    if mswitch is not None:
      protocol = mswitch.group(1)
      model = mswitch.group(2)
      data_hex = mswitch.group(3)
      if protocol == "arctech":
        data = int(data_hex, 16)
        house = int( ( data & 0xFFFFFFC0 ) >> 6)
        group = int( ( data & 0x00000020 ) >> 5)
        method = int( ( data & 0x00000010 ) >> 4)
        unit = int( (data & 0x0000000F) + 1)
        
        # Fix for mismatch between what is recognized and what is required to send a message. E.g. A selflearning-switch is detected as model selflearning and not selflearning-switch
        if model == "selflearning":
          model = "selflearning-switch"  
        for s in listeners:
          if str(s.protocol) == protocol and s.model == model and s.house == house and s.unit == unit:
            print "Telldus device " + str(s.id) + " changed to state " + str(method)
            with lock:
              shared_dict[s.id] = (datetime.datetime.now(), method)
            deviceType = str(s.__class__.__name__)
            topic = deviceType + "s/tellstick/"+ s.mqttRoom +"/"+ s.mqttDescription
            my_publish(topic, method)
            return
          
        print "Not found in config [protocol:" + str(protocol) + ";model:" + str(model) + ";house:" + str(house) + ";unit:" + str(unit) + ";method:" + str(method) + ";]"
            
    elif msensor is not None:
      protocol = msensor.group(1)
      data_hex = msensor.group(2)
      if protocol == "fineoffset": # Bit 0-3 unidentified, bit 4-11 sensorID, bit 12-15 unidentified scrap, bit 16-23 temp, bit 24-31 humidity, 32-39 unidentified scrap
        data = int(data_hex, 16)
        sensorID = int(( data & 0x0FF0000000 ) >> 28)
        temp = float((data & 0x0000FF0000 ) >> 16) / 10
        humidity = int((data & 0x000000FF00 ) >> 8)
        if humidity == 255:
            model = "temperature"
        else:
            model = "temperaturehumidity"

        for s in sensors: # Maybe not keep looking through all sensors after finding a match.
          if str(s.protocol) == protocol and s.model == model and s.id == sensorID:
            my_publish("sensors/" + s.mqttRoom + "/temperature/" + str(s.id) + "/sensors", temp)
            if model == "temperaturehumidity":
              my_publish("sensors/" + s.mqttRoom + "/humidity/" + str(s.id) + "/sensors", humidity)
            return
        unknownSensor = "Not found in config[class:sensor;protocol:" + str(protocol) + ";id:" + str(id) + ";model:" + str(model)
        if model == "temperature":
          unknownSensor += ";temp:" + str(temp) + ";]"
        elif model == "temperaturehumidity":
          unknownSensor += ";humidity:" + str(humidity) + ";temp:" + str(temp) + ";]" 
              

    
with open(configpath + "/config.yaml", 'r') as stream:
  out = yaml.safe_load(stream)
  print "[info] getting the mqtt settings"
  mqtt_host = out['mqtt']['host']
  mqtt_username = out['mqtt']['authentication']['username']
  mqtt_password = out['mqtt']['authentication']['password']
  mqtt_port = out['mqtt']['port']

  print "[info] getting my sensors"
  sensors = []
  try:
    Sensor = namedtuple("Sensor", "id protocol model mqttRoom")
    for s in out['sensor']:
      mysensor = Sensor(s['device']['id'],s['device']['protocol'], s['device']['model'], s['mqttRoom'])
      sensors.append(mysensor)
  except:
    print "[info] No senors in config"

  print "[info] getting my switches"
  listeners = []
  try:
    device = namedtuple("device", "mqttRoom mqttDescription protocol model house unit id")
    for sw in out['switch']:
      myDevice = device(sw['mqtt']['room'],sw['mqtt']['description'],sw['device']['protocol'],sw['device']['model'],sw['device']['house'],sw['device']['unit'], str(sw['mqtt']['room'] + '/' + sw['mqtt']['description']))
      listeners.append(myDevice)
  except:
    print "[info] No switches in config"

  print "[info] getting my triggers"
  try:
    trigger = namedtuple("trigger", "mqttRoom mqttDescription protocol model house unit id")
    for r in out['trigger']:
      myTrigger = trigger(r['mqtt']['room'],r['mqtt']['description'],r['device']['protocol'],r['device']['model'],r['device']['house'],r['device']['unit'], str(sw['mqtt']['room'] + '/' + sw['mqtt']['description']))
      listeners.append(myTrigger)
  except:
    print "[info] No switches in config"


def action_sub_thread():
    print "start of mqtt sub"
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_username, password=mqtt_password)
    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_forever()

def on_connect(client, userdata, rc):
    client.subscribe("devices/tellstick/+/+")

def mqtt_trigger_handler(room,description,msg):
    for sw in listeners:
      if sw.mqttRoom == room  and  sw.mqttDescription == description:
        now = datetime.datetime.now()
        if bool(shared_dict) and sw.id in shared_dict:
          with lock:
            lastupdated = shared_dict[sw.id]
          lastState = lastupdated[1]
          elapsed = now - lastupdated[0]
        else:
          elapsed = datetime.timedelta(seconds=10)
          lastState = 0
          
        if elapsed > datetime.timedelta(seconds=5) or int(lastState) != int(msg.payload):
          print "MQTT device " + str(sw.id) + " setting state " + str(msg.payload)
          q.put( (sw.protocol, sw.model, sw.house, sw.unit, msg.payload) )
          with lock:
            shared_dict[sw.id] = (datetime.datetime.now(), msg.payload)
        return True
    return False


def on_message(client, userdata, msg):
    m = re.search(r"devices\/tellstick\/([a-zA-Z0-9_]{1,30})\/([a-zA-Z0-9_]{1,30})",msg.topic)
    
    if m:
        if mqtt_trigger_handler(m.group(1),m.group(2),msg) == False:
          print "Not listed trigger in room: [" + m.group(1) + "] with  description: [" + m.group(2)+ "]"
    else:
      print "Recived a topic that wasn't supported topic: ["+ msg.topic + "]" 

def my_publish(topic, message):
    publish.single(topic, payload=message, qos=0, retain=False, hostname=mqtt_host,
    port=mqtt_port, client_id="", keepalive=60, will=None, auth= {'username':mqtt_username, 'password':mqtt_password}, tls=None,
    protocol=mqtt.MQTTv31)

print "start thread 1"
t = threading.Thread(target=action_sub_thread, args = ())
t.daemon = True
t.start()

print "start thread 2"
t2 = threading.Thread(target=reader, args = ())
t2.daemon = True
t2.start()

t3 = threading.Thread(target=writer, args = ())
t3.daemon = True
t3.start()

while 1:
  time.sleep(0.1)
  pass


