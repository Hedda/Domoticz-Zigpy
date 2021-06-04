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
                        <li> ti_cc:  Texas Instruments Z-Stack ZNP protocol (ex: CC253x, CC26x2, CC13x2). </li>
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

        <param field="Mode6" label="Verbors and Debuging" width="150px" required="true" default="None">
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
sys.path.append('/var/lib/domoticz/plugins/Domoticz-Zigpy')
import Domoticz
import asyncio
import threading
import logging


PERSISTENT_DB = 'Data/zigpy'

# There are many different radio libraries but they all have the same API



import zigpy.config as config
LOGGER = logging.getLogger(__name__)

import json
import pathlib

import zigpy.types
from zigpy.zdo import types as zdo_t


class MainListener:
    """
    Contains callbacks that zigpy will call whenever something happens.
    Look for `listener_event` in the Zigpy source or just look at the logged warnings.
    """
    def __init__(self, application, Devices):
        Domoticz.Log("MainListener init App: %s Devices: %s" %(application, Devices))
        self.application = application
        self.domoticzDevices = Devices

    def device_joined(self, device):
        Domoticz.Log(f"Device joined: {device}")
        Domoticz.Debug(" - NwkId: %s" %device.nwk)
        Domoticz.Debug(" - IEEE: %s" %device._ieee)


    def device_announce(self, zigpy_device):
        Domoticz.Log("device_announce Zigpy Device: %s" %(zigpy_device))


    def device_initialized(self, device, *, new=True):
        # Called at runtime after a device's information has been queried.
        # I also call it on startup to load existing devices from the DB.

        LOGGER.info("Device is ready: new=%s, device=%s NwkId: %s IEEE: %s signature=%s", new, device, device.nwk, device._ieee, device.get_signature())   
        if new and device.nwk != 0x0000 and len( device.get_signature()) > 0:     
            domoCreateDevice( self, device._ieee, device.get_signature() )

        for ep_id, endpoint in device.endpoints.items():
            # Ignore ZDO
            if ep_id == 0:
                continue

            # You need to attach a listener to every cluster to receive events
            for cluster in endpoint.in_clusters.values():
                # The context listener passes its own object as the first argument
                # to the callback
                cluster.add_context_listener(self)

    #def device_left(self, device):
    #    pass


    #def device_removed(self, device):
    #    pass


    def cluster_command(self, cluster, command_id, *args):
        #Handle commands received to this cluster.
        # Each object is linked to its parent (i.e. app > device > endpoint > cluster)
        device = cluster.endpoint.device
        Domoticz.Log("cluster_command - Cluster: %s ClusterId: 0x%04x command_id: %s args: %s" %(cluster, cluster.cluster_id, command_id, args))


    def attribute_updated(self, cluster, attribute_id, value):
        # Each object is linked to its parent (i.e. app > device > endpoint > cluster)
        device = cluster.endpoint.device
        Domoticz.Debug("Device Signature: %s" %device.get_signature())
        Domoticz.Debug("Received an attribute update %s=%s on cluster %s from device %s/%s" %( attribute_id, value, cluster, device, device._ieee) )
        Domoticz.Debug("Cluster %04x Attribute: %s value: %s type(%s)" %(cluster.cluster_id, attribute_id, value, type(value)))
        domoMajDevice( self, device._ieee, cluster.cluster_id, attribute_id, value )

async def main( self ):

    import zigpy.config as conf
    # Make sure that we have the quirks embedded.
    import zhaquirks  # noqa: F401

    Domoticz.Log("Entering in main ....")
    if self.domoticzParameters["Mode2"] in ( 'USB', 'DIN'):
        path = self.domoticzParameters["SerialPort"]
    elif self.domoticzParameters["Mode2"] == 'PI':
        path = 'pizigate:%s' %self.domoticzParameters["SerialPort"]
    elif self.domoticzParameters["Mode2"] == 'Wifi':
        path = 'socket://%s:%s' %(self.domoticzParameters["Address"], self.domoticzParameters["Port"])
    else:
        Domoticz.Error("Mode: %s Not implemented Yet" %self.domoticzParameters["Mode2"])
        return

    # Config required to connect to a given device
    device_config = {
        conf.CONF_DEVICE_PATH: path,
    }

    # Config required to setup zigpy
    zigpy_config = {
        conf.CONF_DATABASE: self.domoticzParameters["HomeFolder"] + PERSISTENT_DB + '.db',
        conf.CONF_DEVICE: device_config
    }

    if self.domoticzParameters["Mode1"] == 'zigate':
        from zigpy_zigate.zigbee.application import ControllerApplication

    elif self.domoticzParameters["Mode1"] == 'znp':
        from zigpy_znp.zigbee.application import ControllerApplication

    elif self.domoticzParameters["Mode1"] == 'bellows':
        from bellows.zigbee.application import ControllerApplication

    else:
        Domoticz.Error("Mode: %s Not implemented Yet" %self.domoticzParameters["Mode1"])
        return

    # This is unnecessary unless you want to autodetect the radio module that will work
    # with a given port
    #does_radio_work = await ControllerApplication.probe(conf.SCHEMA_DEVICE(device_config))

    self.zigpyApp = await ControllerApplication.new(
        config=ControllerApplication.SCHEMA(zigpy_config),
        auto_form=True,
        start_radio=True,
    )

    listener = MainListener( self.zigpyApp, self.domoticzDevices )
    self.zigpyApp.add_listener(listener)

    # Have every device in the database fire the same event so you can attach listeners
    for device in self.zigpyApp.devices.values():
        listener.device_initialized(device, new=False)

    # Permit joins for a minute
    await self.zigpyApp.permit(240)
    await asyncio.sleep(240)

    # Run forever
    Domoticz.Log("Starting work loop")
    await asyncio.get_running_loop().create_future()
    Domoticz.Log("Exiting work loop")

class BasePlugin:

    def __init__(self):
        self.zigpyThread = None
        self.zigpyApp = None
        self.domoticzParameters = {}
        self.domoticzDevices = None
        
        logging.basicConfig(level=logging.INFO)     

    def get_devices(self):
        devices = []

        for ieee, dev in self.zigpyApp.devices.items():
            device = {
                "ieee": self._ieee_to_number(ieee),
                "nwk": dev.nwk,
                "endpoints": []
            }
            for epid, ep in dev.endpoints.items():
                if epid == 0:
                    continue
                device["endpoints"].append({
                    "id": epid,
                    "input_clusters": [in_cluster for in_cluster in ep.in_clusters] if hasattr(ep, "in_clusters") else [],
                    "output_clusters": [out_cluster for out_cluster in ep.out_clusters] if hasattr(ep, "out_clusters") else [],
                    "status": "uninitialized" if ep.status == zigpy.endpoint.Status.NEW else "initialized"
                })

            devices.append(device)
        return devices

    def zigpy_thread( self ):
            try:
                Domoticz.Log("Starting the thread")
                asyncio.run( main( self ) )
                Domoticz.Log("Thread ended")

            except Exception as e:
                Domoticz.Error("zigpy_thread - Error on asyncio.run: %s" %e)

    def onStart(self):
        logging.basicConfig(level=logging.DEBUG)
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
        Domoticz.Log("onHeartbeat called")

def domoMajDevice( self, device_ieee, cluster, attribute_id, value ):

    Domoticz.Log("domoMajDevice - Device_ieee: %s cluster: %s attribute_id: %s value: %s" %(device_ieee, cluster, attribute_id, value))
    needed_widget_type = get_type_from_cluster( cluster )

    Domoticz.Debug("---> Cluster to Widget: %s" %needed_widget_type)
    if needed_widget_type is None:
        return

    for unit in device_list_units( self, device_ieee):
        if needed_widget_type != get_TypeName_from_device( self, unit ):
            continue

        if needed_widget_type == 'Lux' and attribute_id == 0x0000:
            Domoticz.Debug("Updating -----> Lux")
            nValue = int(value)
            sValue = str(nValue)
            UpdateDevice(self, unit, nValue, sValue )

        elif needed_widget_type == 'Motion' and attribute_id == 0x0000:
            Domoticz.Debug("Updating-----> Motion")
            if bool(value):
                nValue = 1
                sValue = 'On'
            else:
                nValue = 0
                sValue = 'Off'
            UpdateDevice(self, unit, nValue, sValue )

        elif needed_widget_type == 'Switch' and attribute_id == 0x0000:
            if bool(value):
                nValue = 1
                sValue = 'On'
            else:
                nValue = 0
                sValue = 'Off'
            UpdateDevice(self, unit, nValue, sValue )

def get_TypeName_from_device( self, unit):
    
    MATRIX_TYPENAME = {
        (246,1,0): "Lux",
        (244,73,8): "Motion",
        (244,73,0): "Switch", 
    }

    Type = self.domoticzDevices[ unit ].Type
    Subtype = self.domoticzDevices[ unit ].SubType
    SwitchType = self.domoticzDevices[ unit ].SwitchType

    if ( Type, Subtype, SwitchType ) in MATRIX_TYPENAME:
        Domoticz.Debug("(%s,%s,%s) matching with %s" %(Type, Subtype, SwitchType, MATRIX_TYPENAME[  ( Type, Subtype, SwitchType ) ]))
        return MATRIX_TYPENAME[  ( Type, Subtype, SwitchType ) ]

    return None
    

def device_list_units( self, device_ieee):
    return [ x for x in self.domoticzDevices if self.domoticzDevices[x].DeviceID == str(device_ieee) ]

def UpdateDevice(self, Unit, nValue, sValue ):

    Domoticz.Debug("UpdateDevice - Unit: %s %s:%s" %(Unit, nValue, sValue))

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit not in self.domoticzDevices:
        Domoticz.Error("UpdateDevice Unit %s not found!" %Unit)
        return

    if (self.domoticzDevices[Unit].nValue == nValue) and (self.domoticzDevices[Unit].sValue == sValue):
        return

    Domoticz.Log("UpdateDevice %s %s:%s" %(self.domoticzDevices[Unit].Name, nValue, sValue))
    self.domoticzDevices[Unit].Update( nValue=nValue, sValue=sValue)

def domoCreateDevice( self, device_ieee, device_signature):

    Domoticz.Debug("device_signature: %s" %device_signature)
    for ep in device_signature:
        
        Domoticz.Debug(" --> ep: %s" %ep)
        in_cluster = device_signature[ep]['in_clusters']
        out_cluster = device_signature[ep]['out_clusters']
        for cluster in set(in_cluster+out_cluster):
            Domoticz.Debug("----> Cluster: %s" %cluster)
            widget_type = get_type_from_cluster( cluster )
            Domoticz.Debug("---------> Widget Type: %s" %widget_type)

            if widget_type is None:
                continue
        
            elif widget_type == 'Switch':
                Domoticz.Log("----> Create Switch")
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 244, Subtype_ = 73, Switchtype_ = 0 )

            elif widget_type == 'Lux':
                Domoticz.Debug("----> Create Lux")
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 246, Subtype_ = 1, Switchtype_ = 0 )
                
            elif widget_type == 'Motion':
                Domoticz.Debug("----> Create Motion")
                createDomoticzWidget( self, device_ieee, ep, widget_type, widgetType='Motion')
 
def createDomoticzWidget( self, ieee, ep, cType, widgetType = None,
                         Type_ = None, Subtype_ = None, Switchtype_ = None ): 

    Domoticz.Debug("createDomoticzWidget")
    unit = getFreeUnit(self)
    Domoticz.Debug("--> Unit: %s" %unit)
    widgetName = '%s %s - %s' %(widgetType, ieee, ep )
    Domoticz.Debug("--> widgetName: %s" %widgetName)
    if widgetType:
        Domoticz.Log("Creating device is Domoticz DeviceID:%s Name: %s Unit: %s TypeName: %s" %(ieee, widgetName, unit, widgetType))
        myDev = Domoticz.Device( DeviceID = str(ieee), Name = widgetName, Unit = unit, TypeName = widgetType )

    elif Type_ is not None and Subtype_ is not None and Switchtype_ is not None:
        myDev = Domoticz.Device( DeviceID = str(ieee), Name = widgetName, Unit = unit, Type = Type_, Subtype = Subtype_, Switchtype = Switchtype_ )

    else:
        Domoticz.Error("createDomoticzWidget cannot create widget for %s" %(widgetName))
        return
    
    myDev.Create()
    ID = myDev.ID
    if myDev.ID == -1 :
        Domoticz.Error("Domoticz widget creation failed. Check that Domoticz can Accept New Hardware [%s]" %myDev )



def getFreeUnit(self, nbunit_=1):
    '''
    FreeUnit
    Look for a Free Unit number. If nbunit > 1 then we look for nbunit consecutive slots
    '''
    Domoticz.Debug("getFreeUnit - Devices: %s" %len(self.domoticzDevices))
    return len(self.domoticzDevices) + 1

def get_type_from_cluster( cluster ):
    # return a Widget Type list based on the available Cluster 

    TYPE_LIST = {
        0x0006:'Switch',
        0x0400:'Lux',
        0x0406:'Motion'
    }
    if cluster not in TYPE_LIST:
        return None
    return TYPE_LIST[ cluster ]

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
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
