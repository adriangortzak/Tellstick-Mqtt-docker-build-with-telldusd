import argparse
import sys
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import tellcore.constants as const
import re
import threading
from collections import namedtuple
import ruamel.yaml as yaml

import time
import datetime
from pylibftdi import USB_PID_LIST, USB_VID_LIST, Device as TellStick
sys.path.append('/etc/tellstick/rf433')
from rf433.Protocol import Protocol, Device
from Queue import *

USB_PID_LIST.append(0x0c31)
USB_VID_LIST.append(0x1781)

q = Queue()

baudrate=9600
mydevice = None
tellstick = TellStick(mode='t')
tellstick.flush()
t1 = None
t2 = None
target = []
shared_dict = {}
lock = threading.Lock()

def reader():
    while True:
        data = tellstick.read(1024)
        if data != '':
#            print '<< %s' % data
          parseReading(data)

def writer():
#    print "I'm in writer startup"
    while True:
        item = q.get()
        if item is None:
            break
#        print "I've got something in writer now"
        protocol = item[0]
        model = item[1]
        house = item[2]
        unit = item[3]
        command = item[4]
        msg = ""

        # print protocol
        # print model
        # print house
        # print unit
        # print command
        
        myDevice = Protocol.protocolInstance(protocol)
        myDevice.setModel(model)
        myDevice.setParameters({'house': house, 'unit': unit})
        
        if command == "0":
#          print "command is 0"
          msg = myDevice.stringForMethod(Device.TURNOFF, 0)
        elif command == "1":
#          print "command is 1"
          msg = myDevice.stringForMethod(Device.TURNON, 0)
#        print "before sending"
#        print msg
        if 'S' in msg:
          toSend = 'S%s+' % msg['S']
#          print '>> %s' % toSend.encode('string_escape')
          for x in range(1,6):
            tellstick.write(toSend)
            time.sleep(2) # Make sure you sleep or else it won't like getting another command so soon!
        else:
            print "nothing to send"
            time.sleep(1)
def join():
    # Use of a timeout allows Ctrl-C interruption
    t1.join(timeout=1e6)
    t2.join(timeout=1e6)


def parseReading(msg):
    m = re.search(r"protocol:([a-z]+);model:([a-z]+);data:(.+);", msg)
    if m is not None:
      print "I'm in parser"

      # print m.group(1)
      # print m.group(2)
      # print m.group(3)
      protocol = m.group(1)
      model = m.group(2)
      data_hex = m.group(3)
      print data_hex
      data = int(data_hex, 16)
      house = ( data & 0xFFFFFFC0 ) >> 6
      group = ( data & 0x00000020 ) >> 5
      method = ( data & 0x00000010 ) >> 4
      unit = (data & 0x0000000F) + 1
      
      # print protocol
      # print model
      # print house
      # print group
      # print method
      # print unit

      # Fix for mismatch between what is recognized and what is required to send a message. E.g. A selflearning-switch is detected as model selflearning and not selflearning-switch
      if model == "selflearning":
          model = "selflearning-switch"
          
      for s in switches:
        if str(s.protocol) == protocol and s.model == model and s.house == house and s.unit == unit:
          with lock:
            shared_dict[s.id] = (datetime.datetime.now(), method)
          my_publish("devices/tellstick/"+ s.mqttRoom +"/"+ s.mqttDescription, method)
        else:
            print "Switch was not found in config"
    
with open("/tellstick/config.yaml", 'r') as stream:
  out = yaml.safe_load(stream)
  print "[info] getting the mqtt settings"
  mqtt_host = out['mqtt']['host']
  mqtt_username = out['mqtt']['authentication']['username']
  mqtt_password = out['mqtt']['authentication']['password']
  mqtt_port = out['mqtt']['port']

  print "[info] getting my sensors"
  sensors = []
  try:
    Sensor = namedtuple("Sensor", "id protocol dataType model mqttRoom mqttSensorType")
    for s in out['sensor']:
      mysensor = Sensor(s['id'],s['protocol'],s['dataType'], s['model'], s['mqttRoom'], s['mqttSensorType'])
      sensors.append(mysensor)
  except:
    print "[info] No senors in config"

  print "[info] getting my switches"
  switches = []
  try:
    Switch = namedtuple("Switch", "mqttRoom mqttDescription protocol model house unit id")
    for sw in out['switch']:
      mySwitch = Switch(sw['mqttRoom'],sw['mqttDescription'],sw['protocol'],sw['model'],sw['house'],sw['unit'],sw['id'])
      switches.append(mySwitch)
  except:
    print "[info] No switches in config"

  print "[info] getting my raw triggers"
  raw = []
  try:
    Raw = namedtuple("Raw", "tellstickMessage mqttRoom mqttDescription mqttPayload mqttSensorType")
    for r in out['raw']:
      myRaw = Raw(r['tellstickMessage'],r['mqttRoom'],r['mqttDescription'],r['mqttPayload'],r['mqttSensorType'])
      raw.append(myRaw)
  except:
    print "[info] No switches in config"


METHODS = {const.TELLSTICK_TURNON: 'turn on',
           const.TELLSTICK_TURNOFF: 'turn off',
           const.TELLSTICK_BELL: 'bell',
           const.TELLSTICK_TOGGLE: 'toggle',
           const.TELLSTICK_DIM: 'dim',
           const.TELLSTICK_LEARN: 'learn',
           const.TELLSTICK_EXECUTE: 'execute',
           const.TELLSTICK_UP: 'up',
           const.TELLSTICK_DOWN: 'down',
           const.TELLSTICK_STOP: 'stop'}

EVENTS = {const.TELLSTICK_DEVICE_ADDED: "added",
          const.TELLSTICK_DEVICE_REMOVED: "removed",
          const.TELLSTICK_DEVICE_CHANGED: "changed",
          const.TELLSTICK_DEVICE_STATE_CHANGED: "state changed"}

CHANGES = {const.TELLSTICK_CHANGE_NAME: "name",
           const.TELLSTICK_CHANGE_PROTOCOL: "protocol",
           const.TELLSTICK_CHANGE_MODEL: "model",
           const.TELLSTICK_CHANGE_METHOD: "method",
           const.TELLSTICK_CHANGE_AVAILABLE: "available",
           const.TELLSTICK_CHANGE_FIRMWARE: "firmware"}

TYPES = {const.TELLSTICK_CONTROLLER_TELLSTICK: 'tellstick',
         const.TELLSTICK_CONTROLLER_TELLSTICK_DUO: "tellstick duo",
         const.TELLSTICK_CONTROLLER_TELLSTICK_NET: "tellstick net"}

def raw_event(data, controller_id, cid):
  for r in raw:
    if r.tellstickMessage == data:
        my_publish("sensors/"+ r.mqttRoom +"/"+ r.mqttSensorType +"/"+ r.mqttDescription +"/sensors",r.mqttPayload)

  string = "[RAW] {0} <- {1}".format(controller_id, data)
  print(string)


def sensor_handler(id, protocol,model,dataType,value):
  for s in sensors:
    if str(s.id) == str(id) and s.protocol == protocol and s.model == model and s.dataType == dataType:
      my_publish("sensors/"+ s.mqttRoom +"/"+ s.mqttSensorType  +"/"+str(id)+"/sensors", value)
      return True
  return False


def sensor_event(protocol, model, id_, dataType, value, timestamp, cid):
    if sensor_handler(id_,protocol,model,dataType, value) == False:
        string = "[SENSOR] {0} [{1}/{2}] ({3}) @ {4} <- {5}".format(id_, protocol, model, dataType, timestamp, value)
        print(string)

def action_sub_thread():
    print "start of mqtt sub"
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_username, password=mqtt_password)
    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_forever()


def listen_thread():
    print "start tellstick listen thread"
    try:
        if loop:
            loop.run_forever()
        else:
            import time
            while True:
                core.callback_dispatcher.process_pending_callbacks()
                time.sleep(0.5)
    except KeyboardInterrupt:
        pass


def on_connect(client, userdata, rc):
    client.subscribe("devices/tellstick/+/+")

def mqtt_trigger_handler(room,description,msg):
    print "I'm in trigger handler"
    for sw in switches:
      if sw.mqttRoom == room  and  sw.mqttDescription == description:
#        print "matched room and description"
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
          # print "comparison"
          # print elapsed
          # print datetime.timedelta(seconds=5)
          # print elapsed > datetime.timedelta(seconds=5)
          # print lastupdated[1]
          # print msg.payload
          # print int(lastupdated[1]) != int(msg.payload)
          q.put( (sw.protocol, sw.model, sw.house, sw.unit, msg.payload) )
          print "message put in queue"
        else:
          print "Will not repeat sniffed message"
        return True
    return False


def on_message(client, userdata, msg):
    m = re.search(r"devices\/tellstick\/([a-zA-Z0-9_]{1,30})\/([a-zA-Z0-9_]{1,30})",msg.topic)
    print "received message:"
    print m.group(1)
    print m.group(2)
    print msg.payload
    if m:
        if mqtt_trigger_handler(m.group(1),m.group(2),msg) == False:
          print "Not listed trigger in room: [" + m.group(1) + "] with  description: [" + m.group(2)+ "]"
    else:
      print "Recived a topic that wasn't supported topic: ["+ msg.topic + "]" 

def my_publish(topic, message):
    publish.single(topic, payload=message, qos=0, retain=False, hostname=mqtt_host,
    port=mqtt_port, client_id="", keepalive=60, will=None, auth= {'username':mqtt_username, 'password':mqtt_password}, tls=None,
    protocol=mqtt.MQTTv31)

def find_device(device, devices):
    for d in devices:
        print d
        if str(d.id) == device or d.name == device:
            return d
    print("Device '{}' not found".format(device))
    return None

print "start thread 1"
t = threading.Thread(target=action_sub_thread, args = ())
t.daemon = True
t.start()

print "start thread 2"
t2 = threading.Thread(target=reader, args = ())
t2.daemon = True
t2.start()

t3 = threading.Thread(target=writer(), args = ())
t3.daemon = True
t3.start()

while 1:
   pass


