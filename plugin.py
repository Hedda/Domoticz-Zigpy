"""
<plugin key="Zigpy" name="Zigpy plugin" author="pipiche38" version="0.0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2> Plugin Zigpy for Domoticz </h2><br/>
            <h3> Short description </h3>
                This plugin allow Domoticz to access to the Zigbee worlds of devices via zigpy library and the associated Radio libs.<br/>
            <h3> Configuration </h3>
                You can use the following parameter to interact with the Zigbee Radio Hardware:<br/>
                <ul style="list-style-type:square">
                    <li> Zigbee Radio Hardware </li>
                    <ul style="list-style-type:square">
                        <li> ezsp: 	 Silicon Labs EmberZNet protocol (ex; Elelabs, HUSBZB-1, Telegesis). </li>
                        <li> deconz: dresden elektronik deCONZ protocol: ConBee I/II, RaspBee I/II. </li>
                        <li> znp:  Texas Instruments Z-Stack ZNP protocol (ex: CC253x, CC26x2, CC13x2). </li>
                        <li> zigate: ZiGate Controller. You'll have to select between PiZiGate, ZiGate USB-TTL, ZiGate WiFi. </li>
                        <li> xbee: 	 Digi XBee ZB Coordinator Firmware protocol (Digi XBee Series 2, 2C, 3) </li>
                    </ul>
                </ul>
                <ul style="list-style-type:square">
                    <li> Model: Wifi</li>
                    <ul style="list-style-type:square">
                        <li> IP : For Wifi, the IP address. </li>
                        <li> Port: For Wifi,  port number. </li>
                    </ul>
                        <li> Model USB ,  PI or DIN:</li>
                    <ul style="list-style-type:square">
                        <li> Serial Port: this is the serial port where your Radio hardware is connected. (The plugin will provide you the list of possible ports)</li>
                    </ul>
                    <li> Initialize Radio Hardware with plugin: This is a required step, with a new Radio device or if you have done an Erase EEPROM. This will for instance create a new ZigBee Network. </li>
                </ul>
    </description>

    <params>
        <param field="Mode1" label="Radio Hardware Type" width="75px" required="true" default="None">
            <options>
                <option label="zigate (ZiGate controller)" value="zigate" default="None" />
                <option label="znp (Texas Instruments ZNP)" value="znp" default="None" />
                <option label="bellows (Silicon Labs EM35x ('Ember') and EFR32 ('Mighty Gecko') )" value="bellows" default="None" />
            </options>
        </param>

        <param field="Mode2" label="Radio Hardware sub-type (if applicable)" width="75px" required="true" default="None">
            <options>
                <option label="USB" value="USB" default="true" />
                <option label="DIN" value="DIN" />
                <option label="PI" value="PI" />
                <option label="Wifi" value="Wifi"/>
                <option label="None" value="None"/>
            </options>
        </param>

        <param field="Address" label="IP address" width="150px" required="true" default="0.0.0.0"/>

        <param field="Port" label="Port" width="150px" required="true" default="9999"/>
        
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/ttyUSB0"/>

        <param field="Mode3" label="Initialize Radio controller (Erase Memory) " width="75px" required="true" default="False" >
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False" default="true" />
            </options>
        </param>

        <param field="Mode4" label="Listening port for Web Admin GUI " width="75px" required="true" default="9440" />

        <param field="Mode6" label="Verbors and Loging" width="150px" required="true" default="None">
            <options>
                        <option label="None" value="0"  default="true"/>
                        <option label="Plugin Verbose" value="2"/>
                        <option label="Domoticz Plugin" value="4"/>
                        <option label="Domoticz Devices" value="8"/>
                        <option label="Domoticz Connections" value="16"/>
                        <option label="Verbose+Plugin+Devices" value="14"/>
                        <option label="Verbose+Plugin+Devices+Connections" value="30"/>
                        <option label="Domoticz Framework - All (useless but in case)" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import sys
sys.path.append('/usr/lib/python3.9/site-packages')
sys.path.append('/var/lib/domoticz/plugins/Domoticz-Zigpy/Zigpy-Libs')

import asyncio
import threading
import logging

import Domoticz
try:
    from Domoticz import Devices, Parameters
except ImportError:
    pass


# There are many different radio libraries but they all have the same API


import zigpy.config as config
LOGGER = logging.getLogger(__name__)

import json
import pathlib

import zigpy.types
from zigpy.zdo import types as zdo_t

class BasePlugin:

    def __init__(self):
        self.zigpyThread = None
        self.zigpyApp = None
        self.domoticzParameters = {}
        self.domoticzDevices = None
        
        logging.basicConfig(level=logging.INFO)     


    def zigpy_thread( self ):

        from Modules.handle_thread_error import handle_thread_error
        from Modules.zp_main import main

        try:
            Domoticz.Log("Starting the thread")
            asyncio.run( main( self ) )
            Domoticz.Log("Thread ended")

        except Exception as e:
            handle_thread_error( self, e)
            Domoticz.Error("zigpy_thread - Error on asyncio.run: %s" %e)

    def onStart(self):

        logging.basicConfig(level=logging.INFO)
        self.domoticzParameters = dict(Parameters)
        DumpConfigToLog()
        self.domoticzDevices = Devices

        Domoticz.Log("onStart called")
        self.zigpyThread = threading.Thread(
                            name="ZigpyThread", 
                            target=BasePlugin.zigpy_thread,
                            args=(self,))
        self.zigpyThread.start()
            
    def onStop(self):
        Domoticz.Log("onStop called")
        self.zigpyApp.shutdown()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        #Domoticz.Log("onHeartbeat called")
        pass


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
