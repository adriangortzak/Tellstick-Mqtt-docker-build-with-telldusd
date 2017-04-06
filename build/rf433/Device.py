# -*- coding: utf-8 -*-

class Device(object):
	"""
	A base class for a device. Any plugin adding devices must subclass this class.
	"""
	TURNON  = 1  #: Device flag for devices supporting the on method.
	TURNOFF = 2  #: Device flag for devices supporting the off method.
	BELL = 4     #: Device flag for devices supporting the bell method.
	DIM = 16     #: Device flag for devices supporting the dim method.
	LEARN = 32   #: Device flag for devices supporting the learn method.
	UP = 128     #: Device flag for devices supporting the up method.
	DOWN = 256   #: Device flag for devices supporting the down method.
	STOP = 512   #: Device flag for devices supporting the stop method.
	RGBW = 1024  #: Device flag for devices supporting the rgbw method.
	THERMOSTAT = 2048  #: Device flag for devices supporting thermostat methods.

	UNKNOWN = 0                 #: Sensor type flag for an unknown type
	TEMPERATURE = 1             #: Sensor type flag for temperature
	HUMIDITY = 2                #: Sensor type flag for humidity
	RAINRATE = 4                #: Sensor type flag for rain rate
	RAINTOTAL = 8               #: Sensor type flag for rain total
	WINDDIRECTION = 16          #: Sensor type flag for wind direction
	WINDAVERAGE	= 32            #: Sensor type flag for wind average
	WINDGUST = 64               #: Sensor type flag for wind gust
	UV = 128                    #: Sensor type flag for uv
	WATT = 256                  #: Sensor type flag for watt
	LUMINANCE = 512             #: Sensor type flag for luminance
	DEW_POINT = 1024            #: Sensor type flag for dew point
	BAROMETRIC_PRESSURE = 2048  #: Sensor type flag for barometric pressure

	SCALE_UNKNOWN = 0
	SCALE_TEMPERATURE_CELCIUS = 0
	SCALE_TEMPERATURE_FAHRENHEIT = 1
	SCALE_HUMIDITY_PERCENT = 0
	SCALE_RAINRATE_MMH = 0
	SCALE_RAINTOTAL_MM = 0
	SCALE_WIND_VELOCITY_MS = 0
	SCALE_WIND_DIRECTION = 0
	SCALE_UV_INDEX = 0
	SCALE_POWER_KWH = 0
	SCALE_POWER_WATT = 2
	SCALE_LUMINANCE_PERCENT = 0
	SCALE_LUMINANCE_LUX = 1
