
import Domoticz

def get_TypeName_from_device( self, unit):

    MATRIX_TYPENAME = {
        (246,1,0): "Lux",
        (244,73,8): "Motion",
        (244,73,0): "Switch",
        (80,5,0): 'Temp',
        (243,26,0): 'Baro',
        (81,1,0): 'Humi',
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



def get_type_from_cluster( cluster ):
    # return a Widget Type list based on the available Cluster 

    TYPE_LIST = {
        0x0006: 'Switch',
        0x0008: 'LvlControl',
        0x0102: 'Venetian',
        0x0400: 'Lux',
        0x0402: 'Temp',
        0x0403: 'Baro',
        0x0405: 'Humi',
        0x0406: 'Motion'
    }
    if cluster not in TYPE_LIST:
        return None
    return TYPE_LIST[ cluster ]

