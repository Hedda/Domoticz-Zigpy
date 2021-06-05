
import logging
import Domoticz
import asyncio 

from Classes.zp_listener import MainListener
from Modules.plugin_consts import PERSISTENT_DB

async def main( self ):

    logging.basicConfig(level=logging.DEBUG)  

    import zigpy.config as conf

    # Make sure that we have the quirks embedded.
    try:
        import zhaquirks  # noqa: F401
        Domoticz.Debug( "Module zhaquirks loaded")
    except:
        Domoticz.Error( "Module zhaquirks not loaded")

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

