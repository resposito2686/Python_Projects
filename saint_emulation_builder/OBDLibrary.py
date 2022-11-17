"""
OBD2/CAN11 Frame Format:
    S | FH | FH | #B | M | PID | A | B | C | D | XX

OBD2/CAN29 Frame Format:
    S | FH | FH | FH | FH | #B | M | PID | A | B | C | D | XX

S: Saint frame header
    50 = RX
    51 = RX with timestamp
    52 = TX
    53 = TX with timestamp

FH: CAN frame header
    07 DF = Receive CAN11
    07 E8 = Transmit CAN11
    98 DB 33 F1 = Receive CAN29
    98 DB 33 F1 = Transmit CAN29

#B: Number of Data Bytes
    Includes Mode and PID Bytes

M: Mode
    01 = Current Data
    03 = DTC
    09 = VIN

PID: Parameter ID

A, B, C, D: Data Bytes

XX: Unused
"""

#: Abbreviation dictionary for each PID.
#: {abbreviation (PID) : full name}
OBD_ABBREVIATIONS = {

    #: Unit  : boolean
    #: Range : [0, 1]
    'MIL': 'Malfunction Indicator Lamp',

    #: Unit  : revolutions/minute
    #: Range : [0, 16383]
    'RPM': 'RPM',

    #: Unit  : km/hour
    #: Range : [0, 255]
    'VSS': 'Vehicle Speed',

    #: Unit  : percentage (%)
    #: Range : [0, 100]
    'CEL': 'Engine Load',

    #: Unit  : °C
    #: Range : [-40, 215]
    'ECT': 'Engine Coolant Temp',

    #: Unit  : grams/second
    #: Range : [0, 655.35]
    'MAF': 'Mass Air Flow',

    #: Unit  : percentage (%)
    #: Range : [0, 100]
    'TP': 'Throttle Position',
    
    #: Unit  : seconds
    #: Range : [0, 65535]
    'TES': 'Time since Engine Start',

    #: Unit  : km
    #: Range : [0, 65535]
    'DMA': 'Distance MIL Active',

    #: Unit  : kPa
    #: Range : [0, 655350]
    'FRP': 'Fuel Rail Pressure',

    #: Unit  : percentage (%)
    #: Range : [0, 100]
    'FLI': 'Fuel Level Input',

    #: Unit  : km
    #: Range : [0, 65535]
    'DDC': 'Distance DTC Cleared',
    
    #: Unit  : ratio
    #: Range : [0, 1.99]
    'ACE': 'Air Commanded Equivalence Ratio',

    #: Unit  : minutes
    #: Range : [0, 65535]
    'RMA': 'Engine Runtime MIL Active',

    #: Unit  : minutes
    #: Range : [0, 65535]
    'RDA': 'Engine Runtime DTC Active',

    #: Unit  : state encoded
    #: Unit  : {0:None, 1:Gasoline, 2:Methanol, 3:Ethanol, 4:Diesel, 6:Natural Gas, 8:Electric}
    #: Range : [0, 255]
    'FT': 'Fuel Type',

    #: Unit  : °C
    #: Range : [-40, 215]
    'EOT': 'Engine Oil Temperature',

    #: Unit  : liters/hour
    #: Range : [0, 3276.75]
    'EFR': 'Engine Fuel Rate',

    #: Fields : [Run Time, Idle Time, PTO Run Time]
    #: Unit   : seconds
    #: Range  : [[0, 4294967294], [0, 4294967294], [0, 4294967294]]
    'ERT': 'Engine Run Time',

    #: Fields : [DEF Concentration, DEF Temperature, DEF Level]
    #: Unit   : [percentage (%), °C, percentage (%)]
    #: Range  : [[0, 63.75], [-40, 215], [0, 100]]
    'DEF': 'Diesel Exhaust Fluid',
    
    #: Unit  : grams/second
    #: Range : [0, 1310.7]
    'FR': 'Fuel Rate',

    #: Unit  : km
    #: Range : [0, 429496729.5]
    'ODO': 'Odometer',

    #: Unit  : Vehicle Identification Number
    'VIN': 'VIN',
    
    #: Unit  : Diagnostic Trouble Code
    #: Range : [[P0000, P3FFF], [C0000, C3FFF], [B0000, B3FFF], [U0000, U3FFF]]
    'DTC': 'Active DTCs'
}


#: Minimum value each PID can have.
#: {PID : minimum value}
OBD_MIN_VALUE = {
    'MIL': 0,
    'RPM': 0,
    'VSS': 0,
    'CEL': 0,
    'ECT': -40,
    'MAF': 0,
    'TP': 0,
    'TES': 0,
    'DMA': 0,
    'FRP': 0,
    'FLI': 0,
    'DDC': 0,
    'ACE': 0,
    'RMA': 0,
    'RDA': 0,
    'FT': 0,
    'EOT': -40,
    'EFR': 0,
    'ERT': (0, 0, 0),
    'DEF': (0, -40, 0),
    'FR': 0,
    'ODO': 0
}


#: Maximum value each PID can have.
#: {PID : maximum value}
OBD_MAX_VALUE = {
    'MIL': 1,
    'RPM': 16383,
    'VSS': 255,
    'CEL': 100,
    'ECT': 215,
    'MAF': 655.35,
    'TP': 100,
    'TES': 65535,
    'DMA': 65535,
    'FRP': 655350,
    'FLI': 100,
    'DDC': 65535,
    'ACE': 1.99,
    'RMA': 65535,
    'RDA': 65535,
    'FT': 255,
    'EOT': 215,
    'EFR': 3276.75,
    'ERT': (4294967295, 4294967295, 4294967295),
    'DEF': (63.75, 215, 100),
    'FR': 1310.7,
    'ODO': 429496729.5
}


#: Scaling multiplier for each PID.
#: All scaling is done via multiplication except for PIDs that have an 'offset' scaling unit.
#: See OBD_SCALING_UNIT for mor detail.
#: {PID : scaling multiplier}
OBD_SCALING = {
    'MIL': 1,
    'RPM': 4,
    'VSS': 1,
    'CEL': (255 / 100),
    'ECT': 40,
    'MAF': 100,
    'TP': (255 / 100),
    'TES': 1,
    'DMA': 1,
    'FRP': 0.1,
    'FLI': (255 / 100),
    'DDC': 1,
    'ACE': 32786.88,
    'RMA': 1,
    'RDA': 1,
    'FT': 1,
    'EOT': 40,
    'EFR': 20,
    'ERT': (1, 1, 1),
    'DEF': (4, 40, (255 / 100)),
    'FR': 50,
    'ODO': 10

}


#: Scaling unit type for each PID, which determines the operation used to scale the PIDs value. 'int' uses
#:  multiplication, 'float' and 'percent' use floating point multiplication which is then rounded. 'offset' uses
#:  addition.
#: {PID : scaling type}
OBD_SCALING_UNIT = {
    'MIL': 'int',
    'RPM': 'int',
    'VSS': 'int',
    'CEL': 'percent',
    'ECT': 'offset',
    'MAF': 'float',
    'TP': 'percent',
    'TES': 'int',
    'DMA': 'int',
    'FRP': 'float',
    'FLI': 'percent',
    'DDC': 'int',
    'ACE': 'float',
    'RMA': 'int',
    'RDA': 'int',
    'FT': 'int',
    'EOT': 'offset',
    'EFR': 'float',
    'ERT': ('int', 'int', 'int'),
    'DEF': ('float', 'offset', 'percent'),
    'FR': 'float',
    'ODO': 'float'
}


#: Hexadecimal identifier of each PID.
#: {PID : Hex ID}
OBD_PID = {
    'MIL': '01',
    'RPM': '0C',
    'VSS': '0D',
    'CEL': '04',
    'ECT': '05',
    'MAF': '10',
    'TP': '11',
    'TES': '1F',
    'DMA': '21',
    'FRP': '23',
    'FLI': '2F',
    'DDC': '31',
    'ACE': '44',
    'RMA': '4D',
    'RDA': '4E',
    'FT': '51',
    'EOT': '5C',
    'EFR': '5E',
    'ERT': '7F',
    'DEF': '9B',
    'FR': '9D',
    'ODO': 'A6'
}


#: The number of bytes each PID needs to encode in the CAN frame.
#: {PID : # of bytes}
OBD_MSG_BYTES = {
    'MIL': 6,
    'RPM': 4,
    'VSS': 3,
    'CEL': 3,
    'ECT': 3,
    'MAF': 4,
    'TP': 3,
    'TES': 4,
    'DMA': 4,
    'FRP': 4,
    'FLI': 3,
    'DDC': 4,
    'ACE': 4,
    'RMA': 4,
    'RDA': 4,
    'FT': 3,
    'EOT': 3,
    'EFR': 4,
    'ERT': 15,
    'DEF': 6,
    'FR': 4,
    'ODO': 6
}


OBD_SUPPORTED_PIDS = ('00', '20', '40', '60', '80', 'A0')


class InvalidParameter(Exception):
    """
    Raised when an invalid PID has been entered. A valid PID must have: abbreviation, min value, 
    max value, scaling.
    """
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'\'{self.parameter}\' is an invalid parameter name.'


class InvalidVIN(Exception):
    """
    Raised when an invalid VIN has been entered. a valid vin must be a string 17 characters long.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'\'{self.value}\' is an invalid VIN. VIN must contain 17 characters.'
    

class InvalidDTC(Exception):
    """
    Raised when an invalid DTC has been entered. A valid DTC must start with P, C, B, or U and be 5 
    characters long.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'\'{self.value}\' is an invalid DTC.'


class InvalidCANID(Exception):
    """
    Raised when an invalid CAN ID number is entered. A valid CAN ID must be 11 or 29.
    """
    def __init__(self, can_id):
        self.can_id = can_id

    def __str__(self):
        return f'\'{self.can_id}\' is an invalid CAN ID, must be 11 or 29'


class InvalidScaling(Exception):
    """
    Raised when a parameter does not have a scaling unit.
    """
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'\'{self.parameter}\' has no associated scaling unit.'
    

class InvalidGroupPID(Exception):
    """
    Raised if a group file is created for an unsupported PID.
    """
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'\'{self.parameter}\' is not a valid for a group file.'
