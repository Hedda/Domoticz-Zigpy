
import Domoticz
from Modules.domo_tools import get_TypeName_from_device, device_list_units, get_type_from_cluster

def domoMajDevice( self, device_ieee, cluster, attribute_id, value ):

    Domoticz.Debug("domoMajDevice - Device_ieee: %s cluster: %s attribute_id: %s value: %s" %(device_ieee, cluster, attribute_id, value))
    needed_widget_type = get_type_from_cluster( cluster )

    #Domoticz.Debug("---> Cluster to Widget: %s" %needed_widget_type)
    #Domoticz.Debug("---> Attribute 0x%04x %s" %(attribute_id, attribute_id))
    if needed_widget_type is None:
        return

    #Domoticz.Debug("--> Unit list: %s" %device_list_units( self, device_ieee))

    for unit in device_list_units( self, device_ieee):
        #Domoticz.Debug("-------- Checking unit: %s" %unit)
        if needed_widget_type != get_TypeName_from_device( self, unit ):
            #Domoticz.Debug("------------ %s != %s" %(needed_widget_type, get_TypeName_from_device( self, unit )))
            continue

        #Domoticz.Debug("---- Unit %d found !!" %unit)

        if needed_widget_type == 'Lux' and attribute_id == 0x0000:
            Domoticz.Debug("Updating -----> Lux")
            nValue = int(value)
            sValue = str(nValue)
            UpdateDevice(self, unit, nValue, sValue )
            break

        elif needed_widget_type == 'Motion' and attribute_id == 0x0000:
            Domoticz.Debug("Updating-----> Motion")
            if bool(value):
                nValue = 1
                sValue = 'On'
            else:
                nValue = 0
                sValue = 'Off'
            UpdateDevice(self, unit, nValue, sValue )
            break

        elif needed_widget_type == 'Switch' and attribute_id == 0x0000:
            if bool(value):
                nValue = 1
                sValue = 'On'
            else:
                nValue = 0
                sValue = 'Off'
            UpdateDevice(self, unit, nValue, sValue )
            break

        elif needed_widget_type == 'Humi' and attribute_id == 0x0000:
            nValue = int(value/100)
            # Humidity Status
            if nValue < 40:
                humiStatus = 2
            elif 40 <= nValue < 70:
                humiStatus = 1
            else:
                humiStatus = 3
            sValue = str(humiStatus)
            Domoticz.Debug("-->Humi %s:%s" %(nValue, sValue))
            UpdateDevice(self, unit, nValue, sValue )
            break

        elif needed_widget_type == 'Baro' and attribute_id == 0x0000:
            nValue = int( value)
            if nValue < 1000:
                sValue = '%s;4' %nValue # RAIN
            elif nValue < 1020:
                sValue = '%s;3' %nValue # CLOUDY
            elif nValue < 1030:
                sValue = '%s;2' %nValue # PARTLY CLOUDY
            else:
                sValue = '%s;1' %nValue # SUNNY
            Domoticz.Debug("-->Baro %s:%s" %(nValue, sValue))
            UpdateDevice(self, unit, nValue, sValue )
            break

        elif needed_widget_type == 'Temp' and attribute_id == 0x0000:
            nValue = round(int(value)/100,1)
            sValue = str(nValue)
            Domoticz.Debug("-->Temp %s:%s" %(nValue, sValue))
            UpdateDevice(self, unit, int(nValue), sValue )
            break


def UpdateDevice(self, Unit, nValue, sValue ):

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit not in self.domoticzDevices:
        Domoticz.Error("UpdateDevice Unit %s not found!" %Unit)
        return

    if (self.domoticzDevices[Unit].nValue == nValue) and (self.domoticzDevices[Unit].sValue == sValue):
        return

    Domoticz.Log("UpdateDevice Devices[%s].Name: %s --> %s:%s" %(Unit, self.domoticzDevices[Unit].Name, nValue, sValue))
    self.domoticzDevices[Unit].Update( nValue=nValue, sValue=sValue)


