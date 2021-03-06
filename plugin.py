"""
<plugin key="Zigpy" name="Zigpy plugin" author="pipiche38" version="0.0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2> Plugin Zigate for Domoticz </h2><br/>
    <h3> Short description </h3>
           This plugin allow Domoticz to access to the Zigate (Zigbee) worlds of devices.<br/>
    <h3> Configuration </h3>
          You can use the following parameter to interact with the Zigate:<br/>
    <ul style="list-style-type:square">
            <li> Model: Wifi</li>
            <ul style="list-style-type:square">
                <li> IP : For Wifi Zigate, the IP address. </li>
                <li> Port: For Wifi Zigate,  port number. </li>
                </ul>
                <li> Model USB ,  PI or DIN:</li>
            <ul style="list-style-type:square">
                <li> Serial Port: this is the serial port where your USB or DIN Zigate is connected. (The plugin will provide you the list of possible ports)</li>
                </ul>
            <li> Initialize ZiGate with plugin: This is a required step, with a new ZiGate or if you have done an Erase EEPROM. This will for instance create a new ZigBee Network. </li>
    </ul>
    <h3> Support </h3>
    Please use first the Domoticz forums in order to qualify your issue. Select the ZigBee or Zigate topic.
    </description>
    <params>
        <param field="Mode1" label="Zigate Model" width="75px" required="true" default="None">
            <options>
                <option label="USB" value="USB" default="true" />
                <option label="DIN" value="DIN" />
                <option label="PI" value="PI" />
                <option label="Wifi" value="Wifi"/>
                <option label="None" value="None"/>
            </options>
        </param>
        <param field="Address" label="IP" width="150px" required="true" default="0.0.0.0"/>
        <param field="Port" label="Port" width="150px" required="true" default="9999"/>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/ttyUSB0"/>

        <param field="Mode3" label="Initialize ZiGate (Erase Memory) " width="75px" required="true" default="False" >
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


import Domoticz
import asyncio
import threading
import logging

# There are many different radio libraries but they all have the same API
from zigpy_zigate.zigbee.application import ControllerApplication


import zigpy.config as config
LOGGER = logging.getLogger(__name__)

import json
import pathlib

import zigpy.types
from zigpy.zdo import types as zdo_t

class JSONPersistingListener:
    def __init__(self, database_file, application):
        self._database_file = pathlib.Path(database_file)
        self._application = application

        self._db = {'devices': {}}

    def device_joined(self, device):
        self.raw_device_initialized(device)

    def device_initialized(self, device):
        # This is passed in a quirks device
        pass

    def device_left(self, device):
        self._db['devices'].pop(str(device.ieee))
        self._dump()

    def raw_device_initialized(self, device):
        self._db['devices'][str(device.ieee)] = self._serialize_device(device)
        self._dump()

    def device_removed(self, device):
        self._db['devices'].pop(str(device.ieee))
        self._dump()

    def attribute_updated(self, cluster, attrid, value):
        self._dump()

    def _serialize_device(self, device):
        obj = {
            'ieee': str(device.ieee),
            'nwk': device.nwk,
            'status': device.status,
            'node_descriptor': None if not device.node_desc.is_valid else list(device.node_desc.serialize()),
            'endpoints': [],
        }

        for endpoint_id, endpoint in device.endpoints.items():
            if endpoint_id == 0:
                continue  # Skip zdo

            endpoint_obj = {}
            endpoint_obj['id'] = endpoint_id
            endpoint_obj['status'] = endpoint.status
            endpoint_obj['device_type'] = getattr(endpoint, 'device_type', None)
            endpoint_obj['profile_id'] = getattr(endpoint, 'profile_id', None)
            endpoint_obj['output_clusters'] = [cluster.cluster_id for cluster in endpoint.out_clusters.values()]
            endpoint_obj['input_clusters'] = [cluster.cluster_id for cluster in endpoint.in_clusters.values()]

            obj['endpoints'].append(endpoint_obj)

        return obj

    def _dump(self):
        devices = []

        for device in self._application.devices.values():
            devices.append(self._serialize_device(device))

        existing = self._database_file.read_text()
        new = json.dumps({'devices': devices}, separators=(', ', ': '), indent=4)

        # Don't waste writes
        if existing == new:
            return

        self._database_file.write_text(new)

    def load(self):
        try:
            state_obj = json.loads(self._database_file.read_text())
        except FileNotFoundError:
            Domoticz.Error('Database is empty! Creating an empty one...')
            self._database_file.write_text('')

            state_obj = {'devices': []}

        for obj in state_obj['devices']:
            ieee = zigpy.types.named.EUI64([zigpy.types.uint8_t(int(c, 16)) for c in obj['ieee'].split(':')][::-1])

            assert obj['ieee'] in repr(ieee)

            device = self._application.add_device(ieee, obj['nwk'])
            device.status = zigpy.device.Status(obj['status'])

            if 'node_descriptor' in obj and obj['node_descriptor'] is not None:
                device.node_desc = zdo_t.NodeDescriptor.deserialize(bytearray(obj['node_descriptor']))[0]

            for endpoint_obj in obj['endpoints']:
                endpoint = device.add_endpoint(endpoint_obj['id'])
                endpoint.profile_id = endpoint_obj['profile_id']
                device_type = endpoint_obj['device_type']

                try:
                    if endpoint.profile_id == 260:
                        device_type = zigpy.profiles.zha.DeviceType(device_type)
                    elif endpoint.profile_id == 49246:
                        device_type = zigpy.profiles.zll.DeviceType(device_type)
                except ValueError:
                    pass

                endpoint.device_type = device_type
                endpoint.status = zigpy.endpoint.Status(endpoint_obj['status'])

                for output_cluster in endpoint_obj['output_clusters']:
                    endpoint.add_output_cluster(output_cluster)

                for input_cluster in endpoint_obj['input_clusters']:
                    cluster = endpoint.add_input_cluster(input_cluster)


# Use this in place of your radio's ControllerApplication
class JSONControllerApplication(ControllerApplication):
    def __init__(self, config):
        super().__init__(self.SCHEMA(config))

        # Replace the internal SQLite DB listener with our own
        self._dblistener = JSONPersistingListener(self.config['json_database_path'], self)
        self.add_listener(self._dblistener)
        self._dblistener.load()
        self._dblistener._dump()


class MainListener:
    """
    Contains callbacks that zigpy will call whenever something happens.
    Look for `listener_event` in the Zigpy source or just look at the logged warnings.
    """

    def __init__(self, application):
        Domoticz.Log("MainListener init")
        self.application = application

    def device_joined(self, device):
        Domoticz.Log(f"Device joined: {device}")
        Domoticz.Log(" - NwkId: %s" %device.nwk)
        Domoticz.Log(" - IEEE: %s" %device._ieee)


    def device_initialized(self, device, *, new=True):
        """
        Called at runtime after a device's information has been queried.
        I also call it on startup to load existing devices from the DB.
        """
        LOGGER.info("Device is ready: new=%s, device=%s", new, device)

        for ep_id, endpoint in device.endpoints.items():
            # Ignore ZDO
            if ep_id == 0:
                continue

            # You need to attach a listener to every cluster to receive events
            for cluster in endpoint.in_clusters.values():
                # The context listener passes its own object as the first argument
                # to the callback
                cluster.add_context_listener(self)

    def attribute_updated(self, cluster, attribute_id, value):
        # Each object is linked to its parent (i.e. app > device > endpoint > cluster)
        device = cluster.endpoint.device

        LOGGER.info("Received an attribute update %s=%s on cluster %s from device %s",
            attribute_id, value, cluster, device)


async def main():
    #app = await ControllerApplication.new(
    #    config=ControllerApplication.SCHEMA({
    #        "database_path": "/tmp/zigpy.db",
    ##        "device": {
    #            "path": "/dev/null", #/dev/ttyUSBRPI3",
    #        }
    #    }),
    ###    auto_form=True,
    #    start_radio=True,
    #)
    app = await JSONControllerApplication.new(
        config=ControllerApplication.SCHEMA({
            "json_database_path": "/tmp/zigpy.json",
            "device": {
                "path": "/dev/ttyUSBRPI3", #/dev/ttyUSBRPI3",
            }
        }),
        auto_form=True,
        start_radio=True,
    )

    listener = MainListener(app)
    app.add_listener(listener)

    # Have every device in the database fire the same event so you can attach listeners
    for device in app.devices.values():
        listener.device_initialized(device, new=False)

    # Permit joins for a minute
    await app.permit(60)
    await asyncio.sleep(60)

    # Run forever
    await asyncio.get_running_loop().create_future()

class BasePlugin:

    def __init__(self):
        self.zigpyThread = None
        self.zigpyApp = None
        logging.basicConfig(level=logging.DEBUG)     

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
                asyncio.run( main() )
                Domoticz.Log("Thread ended")

            except Exception as e:
                Domoticz.Error("zigpy_thread - Error on asyncio.run: %s" %e)

    def onStart(self):
        logging.basicConfig(level=logging.DEBUG)
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
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
