import argparse
import sys
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import tellcore.telldus as td
import tellcore.constants as const
import re
import threading
from ConfigParser import SafeConfigParser


config = SafeConfigParser()
config.read('/tellstick/config.ini')


mqtt_host = config.get('mqtt','host')
mqtt_username = config.get('mqtt','username')
mqtt_password = config.get('mqtt','password')
mqtt_port = 1883


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


def device_event(id_, method, data, cid):
    method_string = METHODS.get(method, "UNKNOWN METHOD {0}".format(method))
    string = "[DEVICE] {0} -> {1}".format(id_, method_string)
    if method == const.TELLSTICK_DIM:
        string += " [{0}]".format(data)
    print(string)


def device_change_event(id_, event, type_, cid):
    event_string = EVENTS.get(event, "UNKNOWN EVENT {0}".format(event))
    string = "[DEVICE_CHANGE] {0} {1}".format(event_string, id_)
    if event == const.TELLSTICK_DEVICE_CHANGED:
        type_string = CHANGES.get(type_, "UNKNOWN CHANGE {0}".format(type_))
        string += " [{0}]".format(type_string)
    print(string)


def raw_event(data, controller_id, cid):
    m = re.search(r"class:sensor;protocol:([a-z]{1,12});id:([0-9]{1,3});model:temperaturehumidity;humidity:[0-9]{1,2};temp:([0-9]{1,2}.[0-9])", data)
    if m:
        if m.group(1) == "fineoffset" and m.group(2) == "135":
            my_publish("sensors/living_room/temperature/"+str(m.group(2))+"/sensors",m.group(3))
    elif data == "class:command;protocol:arctech;model:selflearning;house:15139302;unit:10;group:0;method:turnon;":
        my_publish("sensors/hall/motion/15139302/sensors",1)
    else:
        string = "[RAW] {0} <- {1}".format(controller_id, data)
        print(string)


def sensor_event(protocol, model, id_, dataType, value, timestamp, cid):
    if id_ == 135 and protocol =="fineoffset" and model=="temperaturehumidity":
        my_publish("sensors/living_room/humidity/"+str(id_)+"/sensors", value)
    elif id_ == 136 and protocol =="fineoffset" and model=="temperature":
        my_publish("sensors/outdoors/temperature/"+str(id_)+"/sensors", value)
    elif id_ == 183 and protocol =="fineoffset" and model=="temperaturehumidity" and dataType == 1:
        my_publish("sensors/bedroom/temperature/"+str(id_)+"/sensors", value)
    elif id_ == 183 and protocol =="fineoffset" and model=="temperaturehumidity" and dataType == 2:
        my_publish("sensors/bedroom/humidity/"+str(id_)+"/sensors", value)
    else:
        string = "[SENSOR] {0} [{1}/{2}] ({3}) @ {4} <- {5}".format(id_, protocol, model, dataType, timestamp, value)
        print(string)



def controller_event(id_, event, type_, new_value, cid):
    event_string = EVENTS.get(event, "UNKNOWN EVENT {0}".format(event))
    string = "[CONTROLLER] {0} {1}".format(event_string, id_)
    if event == const.TELLSTICK_DEVICE_ADDED:
        type_string = TYPES.get(type_, "UNKNOWN TYPE {0}".format(type_))
        string += " {0}".format(type_string)
    elif (event == const.TELLSTICK_DEVICE_CHANGED
          or event == const.TELLSTICK_DEVICE_STATE_CHANGED):
        type_string = CHANGES.get(type_, "UNKNOWN CHANGE {0}".format(type_))
        string += " [{0}] -> {1}".format(type_string, new_value)
    print(string)


try:
    import asyncio
    loop = asyncio.get_event_loop()
    dispatcher = td.AsyncioCallbackDispatcher(loop)
except ImportError:
    loop = None
    dispatcher = td.QueuedCallbackDispatcher()

core = td.TelldusCore(callback_dispatcher=dispatcher)
callbacks = []

callbacks.append(core.register_device_event(device_event))
callbacks.append(core.register_device_change_event(device_change_event))
callbacks.append(core.register_raw_device_event(raw_event))
callbacks.append(core.register_sensor_event(sensor_event))
callbacks.append(core.register_controller_event(controller_event))

def action_sub_thread():
    print "start of mqtt sub"
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_username, password=mqtt_password)
    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_forever()


def listen_thread():
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


def on_message(client, userdata, msg):
    print "Topic: ", msg.topic+ '\nMessage: '+str(msg.payload)
    m = re.search(r"devices\/tellstick\/([a-zA-Z0-9_]{1,30})\/([a-zA-Z0-9_]{1,30})",msg.topic)
    if m:
        if m.group(1) == "living_room" and m.group(2) == "tv_lamp":
            change_device_state('2',str(msg.payload))
        elif m.group(1) == "man_cave" and m.group(2) == "desk_lamp":
            change_device_state('1',str(msg.payload))


def my_publish(topic, message):
     publish.single(topic, payload=message, qos=0, retain=False, hostname=mqtt_host,
    port=mqtt_port, client_id="", keepalive=60, will=None, auth= {'username':mqtt_username, 'password':mqtt_password}, tls=None,
    protocol=mqtt.MQTTv31)


def turn_on_device(id):
    core = td.TelldusCore()
    core.sensors()
    device = find_device(id, core.devices())
    if device is not None:
        device.turn_on()


def turn_off_device(id):
    core = td.TelldusCore()
    device = find_device(id, core.devices())
    if device is not None:
        device.turn_off()


def change_device_state(id,state):
    if state == "1":
        turn_on_device(id)
    elif state == "0":
        turn_off_device(id)


def find_device(device, devices):
    for d in devices:
        print d
        if str(d.id) == device or d.name == device:
            return d
    print("Device '{}' not found".format(device))
    return None


t = threading.Thread(target=action_sub_thread, args = ())
t.daemon = True
t.start()

t2 = threading.Thread(target=listen_thread(), args = ())
t2.daemon = True
t2.start()


while 1:
   pass


