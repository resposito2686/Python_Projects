"""
===============================
AUTHOR        : Robert Esposito
CREATE DATE   : January 27th, 2022
PURPOSE       : This application will generate emulation files for the SAINT Bus Monitor.
===============================
Change History:
    01/27/22 - Version 1.0
    02/02/22 - Version 1.1: Added support for active DTCs.
    02/18/22 - Version 1.2: Added support for PUE Script and PID 1F.
    05/09/22 - Version 2.0: Added GUI to emulation builder.
    08/19/22 - Version 2.1: Changed file format from txt -> json
==================================

"""
import os
import random
import string
import OBDLibrary as obd

#: All emulation files are saved in <Folder containing this script>\SAINT_Emulation\<CAN protocol>
#: <CAN protocol> will be CAN11 or CAN29, depending on which is desired.
PATH = os.path.join(os.path.dirname(__file__), 'SAINT_Emulation')

#: Constants
CAN_29 = 29
CAN_11 = 11
VIN_LEN = 17
DTC_LEN = 5


def build_emulation_file(can_id, **pid_data_pairs):
    """
    Builds the list of strings that will populate the emulation file. The function will iterate through 
    the PID:values pairs and generate a CAN frame containing them. It will also generate a 'PID enabled' 
    CAN frame that marks each PID as active.
    
    A PID must be passed as it's abbreviation listed in obd.OBD_ABBREVIATIONS.

    Values is a list of all values a CAN frame will be generated for. If no value is given, 
    the obd.OBD_MIN_VALUE and obd.OBD_MAX_VALUE will be used instead.
    
    @param can_id: The CAN identifier length. Any value other than 29 will default to 11.
    @param pid_data_pairs: All PID:values pairs, formatted as '<PID>':[<values>].
    @return: _write_file()
    
    == Example ==

        build_emulation_file(can_id=29, RPM=[0, 3000, 8999], VSS=[])

        The emulation file will contain a 'PID enabled' CAN frame that mark RPM and VSS as active, 
        3 frames for each RPM value (0, 3000, and 8999), and 2 frame for the minimum and maximum 
        values of VSS.
    """

    #: List containing the generated CAN frames for each PID:[Values].
    obd_strings = []

    #: List containing the generated 'PID enabled' CAN frames.
    supported_pids = [0, 0, 0, 0, 0, 0]

    #: Assigns can_id to either CAN29 or CAN11.
    #: Creates headers depending on the CAN ID.
    if can_id == CAN_29:
        pid_rx_header = '51 98 DB 33 F1 02 01'
        pid_tx_header = '53 98 DA F1 33 06 41'
    else:
        can_id = CAN_11
        pid_rx_header = '51 07 DF 02 01'
        pid_tx_header = '53 07 E8 06 41'

    for key, value in pid_data_pairs.items():
        key = key.upper()

        #: Checks if the PID is valid.
        if key in obd.OBD_ABBREVIATIONS:

            #: Generates the 'PID enabled' CAN frames to support each (mode 1) PID in kwargs.
            if key in obd.OBD_PID:

                #: Converts PID from a hex value to decimal for bitwise manipulation.
                pid_int = int(obd.OBD_PID[key], 16)

                #: Checks which PID enabled frame the current PID is associated with and sets its corresponding
                #: enable bit to 1.
                #: Formula: 1 << ( (PIDs supported group + 32) - current PID ).
                if pid_int <= int(obd.OBD_SUPPORTED_PIDS[0], 16) + 32:
                    supported_pids[0] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[0], 16) + 32) - pid_int))
                elif pid_int <= int(obd.OBD_SUPPORTED_PIDS[1], 16) + 32:
                    supported_pids[0] |= 1
                    supported_pids[1] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[1], 16) + 32) - pid_int))
                elif pid_int <= int(obd.OBD_SUPPORTED_PIDS[2], 16) + 32:
                    supported_pids[1] |= 1
                    supported_pids[2] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[2], 16) + 32) - pid_int))
                elif pid_int <= int(obd.OBD_SUPPORTED_PIDS[3], 16) + 32:
                    supported_pids[2] |= 1
                    supported_pids[3] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[3], 16) + 32) - pid_int))
                elif pid_int <= int(obd.OBD_SUPPORTED_PIDS[4], 16) + 32:
                    supported_pids[3] |= 1
                    supported_pids[4] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[4], 16) + 32) - pid_int))
                elif pid_int <= int(obd.OBD_SUPPORTED_PIDS[5], 16) + 32:
                    supported_pids[4] |= 1
                    supported_pids[5] |= (1 << ((int(obd.OBD_SUPPORTED_PIDS[5], 16) + 32) - pid_int))
                else:
                    pass

            #: Writes a label that separates each PID in the emulation file.
            obd_strings.append(
                f'=== {obd.OBD_ABBREVIATIONS[key]} ({key}) ===,Transmit,'
                f'=== {obd.OBD_ABBREVIATIONS[key]} ({key}) ===,False')

            #: If there is at least one value, call build_string() with those values.
            if value:
                for v in value:
                    obd_strings.append(build_string(key, v, can_id))

            #: If No value is associated with a PID, call build_string() using minimum and maximum values.
            else:
                try:
                    obd_strings.append(build_string(key, obd.OBD_MIN_VALUE[key], can_id))
                    obd_strings.append(build_string(key, obd.OBD_MAX_VALUE[key], can_id))

                #: Raises exception if parameter doesn't have a minimum or maximum value.
                except KeyError as e:
                    raise obd.InvalidParameter(e)

        #: Raises exception if the PID is invalid or not supported.
        else:
            raise obd.InvalidParameter(key)

    #: Label for 'PID enabled' frames
    pid_strings = ['=== Supported PIDs ===,Transmit,=== Supported PIDs ===,False']

    #: Converts the 'PID enabled' integer values back to hex strings once they have been bitwise manipulated.
    #: Generates the 'PID enabled' frames.
    for i, pid_hex in enumerate(supported_pids):
        pid_hex = str(hex(pid_hex)[2:].upper().zfill(8))
        pid_hex = ' '.join(pid_hex[i:i + 2] for i in range(0, len(pid_hex), 2))
        pid_strings.append(f'{pid_rx_header} {obd.OBD_SUPPORTED_PIDS[i]} 00 00 00 00 00,Transmit,'
                           f'{pid_tx_header} {obd.OBD_SUPPORTED_PIDS[i]} {pid_hex} 00,True')

    #: Calls _write_file() with all the generated CAN frames.
    file_data = pid_strings + obd_strings
    file_data.insert(0, f'CAN{str(can_id)}')
    return _write_file(file_data)


def build_string(parameter, value, can_id, pue=False):
    """
    Builds the receive (rx) and transmit (tx) CAN frames containing the PID and value.

    @param parameter: The parameter ID for the rx and tx frames.
    @param value: The decimal value to be encoded into the tx frame.
    @param can_id: The CAN identifier length.
    @param pue: Flags RPM and TES to be written in group files (used by PUE_Script.py).
    @return: A string containing the rx and tx CAN frames, along with control parameters for the SAINT Bus Monitor. 
             If the parameter is VIN, _create_vin() is returned. 
             If the parameter is DTC, _create_dtc() is returned.
    """

    if parameter == 'VIN':

        #: Checks if the VIN is valid.
        #: Any string containing 17 characters is considered valid.
        if len(value) != VIN_LEN:
            raise obd.InvalidVIN(value)
        else:
            return _create_vin(value, can_id)

    if parameter == 'DTC':
        return _create_dtc(value, can_id)

    #: Checks if any value is outside the minimum and maximum allowed values for the corresponding PID.
    try:

        #: Checks if value is a list.
        if isinstance(value, list):
            for i in range(len(value)):
                if value[i] < obd.OBD_MIN_VALUE[parameter][i]:
                    value[i] = obd.OBD_MIN_VALUE[parameter][i]
                if value[i] > obd.OBD_MAX_VALUE[parameter][i]:
                    value[i] = obd.OBD_MAX_VALUE[parameter][i]
        else:
            if value < obd.OBD_MIN_VALUE[parameter]:
                value = obd.OBD_MIN_VALUE[parameter]
            if value > obd.OBD_MAX_VALUE[parameter]:
                value = obd.OBD_MAX_VALUE[parameter]

    #: Raises exception if parameter doesn't have a minimum or maximum value.
    except KeyError as e:
        raise obd.InvalidParameter(e)

    #: Builds the receive CAN frame.
    rx = _create_rx(parameter, can_id)

    #: Builds the transmit CAN frame.
    tx = _create_tx(parameter, value, can_id, pue)

    #: SAINT Bus Monitor parameter.
    if parameter == 'ERT':
        option = 'Group'
    else:
        option = 'Transmit'

    if pue:
        return f'{rx},Group,{tx},True'

    return f'{rx},{option},{tx},False'


def _create_rx(parameter, can_id):
    """
    Builds the receive CAN frame for the PID passed as argument.

    @param parameter: The parameter ID for the frame.
    @param can_id: The CAN identifier length.
    @return: A string containing the receive CAN frame.
    """

    #: Checks if can_id is CAN11 or CAN29.
    if can_id == CAN_11:
        header_rx = '51 07 DF 02 01'
    elif can_id == CAN_29:
        header_rx = '51 98 DB 33 F1 02 01'
    else:
        raise obd.InvalidCANID(can_id)

    #: Gets the hex value for the PID.
    pid_rx = obd.OBD_PID[parameter]

    #: Fills the rest of the frame with 00 bytes.
    footer_rx = '00 00 00 00 00'

    return f'{header_rx} {pid_rx} {footer_rx}'


def _create_tx(parameter, value, can_id, pue):
    """
    Builds the transmit CAN frame using the PID and value passed in as argument. The value is scaled based on its
    entries in OBD_Library.OBD_SCALING and OBD_Library.OBD_SCALING_UNIT.

    Some PIDs, such as 'MIL' and 'DEF', have their value encoded different that a typical frame. These unique cases are
    also handled here.

    @param parameter: The parameter ID for the frame.
    @param value: The decimal value to be scaled and encoded into the frame.
    @param can_id: The CAN identifier length.
    @param pue: Flags RPM and TES to be written in group files (used by PUE_Script.py).
    @return: A string containing the transmit CAN frame. If the CAN frame requires more than 6 bytes to encode its
    value, _create_group() is called and the file path to the group file is returned instead.
    """

    #: RPM and TES are group files for PUE_Script
    if (parameter == 'RPM' and pue) or (parameter == 'TES' and pue):
        return _create_group(parameter, value, can_id)

    #: Call create_group if PID is 'ERT'
    if parameter == 'ERT':
        return _create_group(parameter, value, can_id)

    #: Checks if can_id is CAN11 or CAN29.
    if can_id == CAN_11:
        header_tx = '53 07 E8'
    elif can_id == CAN_29:
        header_tx = '53 98 DA F1 33'
    else:
        raise obd.InvalidCANID(can_id)

    #: Gets the number of bytes used to encode the value and converts into hex.
    msg_bytes_tx = _convert_to_bytes(obd.OBD_MSG_BYTES[parameter], 1)

    mode_tx = '41'
    pid_tx = obd.OBD_PID[parameter]

    #: Pads the end of the frame with 00 bytes.
    footer_tx = ''
    for i in range(7 - obd.OBD_MSG_BYTES[parameter]):
        footer_tx += ' 00'

    #: Value encoding for MIL.
    if parameter == 'MIL':
        if value > 0:
            data_tx = '80 00 00 00'
        else:
            data_tx = '00 00 00 00'

    #: Value encoding for DEF
    elif parameter == 'DEF':

        #: DEF encodes three values in the same frame.
        if len(value) < 3:
            for i in range(len(value), 3):
                value.append(obd.OBD_MIN_VALUE[parameter][i])
        def_tx = [_convert_to_bytes((value[0] * obd.OBD_SCALING['DEF'][0]), 1),
                  _convert_to_bytes((value[1] + obd.OBD_SCALING['DEF'][1]), 1),
                  _convert_to_bytes((value[2] * obd.OBD_SCALING['DEF'][2]), 1)]
        data_tx = "07 {0}".format(' '.join(def_tx))

    #: PID does not require any special handling.
    else:

        #: Value is scaled and encoded based on the scaling unit.
        if obd.OBD_SCALING_UNIT[parameter] == 'offset':
            data_tx = _convert_to_bytes(value + obd.OBD_SCALING[parameter], obd.OBD_MSG_BYTES[parameter] - 2)
        else:
            data_tx = _convert_to_bytes(value * obd.OBD_SCALING[parameter], obd.OBD_MSG_BYTES[parameter] - 2)

    return f'{header_tx} {msg_bytes_tx} {mode_tx} {pid_tx} {data_tx}{footer_tx}'


def _create_group(parameter, value, can_id):
    """
    Creates a group file for the given PID. This function should only be called on 
    by _create_tx() on PIDs that have specified handling.

    @param parameter: The parameter ID for the frame.
    @param value: The decimal value to be scaled and encoded into the frame.
    @param can_id: The CAN identifier length.
    @return: A string containing the file path of the group file that was created.
    """

    #: Transmission delay between each frame of the group file.
    frame_delay = '0010'

    #: Checks if can_id is CAN11 or CAN29.
    if can_id == CAN_11:
        header_grp = '51 07 E8'
    elif can_id == CAN_29:
        header_grp = '53 98 DA F1 33'
    else:
        raise obd.InvalidCANID(can_id)

    #: Gets the number of bytes used to encode the value and converts into hex.
    msg_bytes_grp = str(hex(obd.OBD_MSG_BYTES[parameter]))[2:].zfill(2).upper()

    pid_grp = obd.OBD_PID[parameter]
    mode_grp = '41'

    #: Calculates the frame number byte for each frame in the frame group.
    frame_grp = ['10']
    for num in range(int(obd.OBD_MSG_BYTES[parameter] / 7)):
        frame_grp.append(str(num + 21))

    #: Pads the end of the last frame with 00 bytes.
    footer_padding = (((int(obd.OBD_MSG_BYTES[parameter] / 7) + 1) * 7) - 1) % obd.OBD_MSG_BYTES[parameter]
    footer_grp = ''
    for i in range(footer_padding):
        footer_grp += ' 00'

    #: Value encoding for ERT.
    if parameter == 'ERT':

        #: ERT encodes three values in the same frame group.
        if len(value) < 3:
            for i in range(len(value), 3):
                value.append(obd.OBD_MIN_VALUE[parameter][i])
        data_tx: list = [str(hex(value[i]))[2:].zfill(8).upper() for i in range(3)]

        for i in range(3):
            data_tx[i] = [data_tx[i][j:j + 2] for j in range(0, 8, 2)]

        #: The group file is named based on the values encoded.
        can_id_str = f'CAN{str(can_id)}'
        file_name = f'{PATH}\\{can_id_str}\\ENGINE_RUNTIME_{value[0]}_{value[1]}_{value[2]}.grp'

        #: Creates the file path if it does not already exist.
        if not (os.path.exists(f'{PATH}\\{can_id_str}')):
            try:
                os.mkdir(f'{PATH}\\{can_id_str}')
            except OSError:
                raise

        #: Writes to the group file.
        with open(file_name, 'w') as f:
            f.write(f'{frame_delay} {header_grp} {frame_grp[0]} {msg_bytes_grp} {mode_grp} {pid_grp} 03 '
                    f'{data_tx[0][0]} {data_tx[0][1]} {data_tx[0][2]}\n'
                    f'{frame_delay} {header_grp} {frame_grp[1]} {data_tx[0][3]} {data_tx[1][0]} {data_tx[1][1]} '
                    f'{data_tx[1][2]} {data_tx[1][3]} {data_tx[2][0]} {data_tx[2][1]}\n'
                    f'{frame_delay} {header_grp} {frame_grp[2]} {data_tx[2][2]} {data_tx[2][3]}{footer_grp}')

        return file_name

    #: Group file needed for RPM and TES when using PUE_Script.py
    if parameter == 'RPM' or parameter == 'TES':

        data_tx: str = _convert_to_bytes(value * obd.OBD_SCALING[parameter], obd.OBD_MSG_BYTES[parameter] - 2)
        can_id_str = f'CAN{str(can_id)}'
        file_name = f'{PATH}\\{can_id_str}\\{parameter}.grp'

        if not (os.path.exists(f'{PATH}\\{can_id_str}')):
            raise OSError

        try:
            with open(file_name, 'w') as f:
                if can_id == CAN_29:
                    f.write(f'0010 53 98 DA F1 33 04 41 {obd.OBD_PID[parameter]} {data_tx} 00 00 00')
                else:
                    f.write(f'0010 53 07 E8 04 41 {obd.OBD_PID[parameter]} {data_tx} 00 00 00')
        except PermissionError:
            pass

        return file_name

    else:
        raise obd.InvalidGroupPID(parameter)


def _create_vin(value, can_id):
    """
    Creates a group file for the given VIN. This is separate from _create_group() 
    because VIN is not a mode 1 request.

    @param value: The Vehicle Identification Number (VIN).
    @param can_id: The CAN identifier length.
    @return: A string containing the file path of the group file that was created.
    """

    #: Transmission delay between each frame of the group file.
    frame_delay = '0001'

    #: Checks if can_id is CAN11 or CAN29.
    #: Creates the rx frame, along with the tx frame header.
    if can_id == CAN_11:
        header_rx = '51 07 DF 02 09 02 00 00 00 00 00'
        header_grp = '50 07 E8'
    elif can_id == CAN_29:
        header_rx = '51 98 DB 33 F1 02 09 02 00 00 00 00 00'
        header_grp = '50 98 DA F1 33'
    else:
        raise obd.InvalidCANID(can_id)

    #: Converts the ASCII value of the VIN into hex.
    data_tx = [hex(ord(d))[2:].zfill(2).upper() for d in value]

    #: The group file is named based on the VIN.
    can_id_str = f'CAN{str(can_id)}'
    file_name = f'{PATH}\\{can_id_str}\\{value}_VIN.grp'

    #: Creates the file path if it does not already exist.
    if not (os.path.exists(f'{PATH}\\{can_id_str}')):
        try:
            os.mkdir(f'{PATH}\\{can_id_str}')
        except OSError:
            raise

    #: Writes to the group file.
    with open(file_name, 'w') as f:
        f.write(f'{frame_delay} {header_grp} 10 14 49 02 01 {data_tx[0]} {data_tx[1]} {data_tx[2]}\n'
                f'{frame_delay} {header_grp} 21 {data_tx[3]} {data_tx[4]} {data_tx[5]} {data_tx[6]} '
                f'{data_tx[7]} {data_tx[8]} {data_tx[9]}\n'
                f'{frame_delay} {header_grp} 22 {data_tx[10]} {data_tx[11]} {data_tx[12]} {data_tx[13]} '
                f'{data_tx[14]} {data_tx[15]} {data_tx[16]}')

    #: Both rx and tx frames, along with the Saint Bus Monitor control variables, are returned.
    return f'{header_rx},Group,{file_name},False'


def _create_dtc(value, can_id):
    """
    Creates a group file for the given DTCs. This is separate from _create_group() 
    because DTC is not a mode 1 request.

    @param value: The list of DTCs.
    @param can_id: The CAN identifier length.
    @return: A string containing the file path of the group file that was created.
    """

    #: Checks if can_id is CAN11 or CAN29.
    #: Creates the rx frame, along with the tx frame header.
    if can_id == CAN_11:
        header_rx = '51 07 DF 01 03 00 00 00 00 00 00'
        header_grp = '50 07 E8'
    elif can_id == CAN_29:
        header_rx = '51 98 DB 33 F1 01 03 00 00 00 00 00 00'
        header_grp = '50 98 DA F1 33'
    else:
        raise obd.InvalidCANID(can_id)

    #: Frame delay of 4ms.
    frame_delay = '0010'

    #: List containing all the DTCs converted to hex.
    #: Each item is 1 byte. This is because each DTC is encoded into 2 bytes that can sometimes be split across
    #: 2 frames.
    dtc_list = []

    for i in value:

        #: Checks the DTC is formatted correctly
        if len(i) < DTC_LEN:
            raise obd.InvalidDTC(i)

        #: Converts the first letter (P, C, B, or U) to an integer value.
        else:
            if i[0].upper() == 'P':
                dtc_type = 0
            elif i[0].upper() == 'C':
                dtc_type = 1
            elif i[0].upper() == 'B':
                dtc_type = 2
            elif i[0].upper() == 'U':
                dtc_type = 3
            else:
                raise obd.InvalidDTC(i)

            #: Checks that each character in the DTC is valid.
            if int(i[1], 16) > 3 or int(i[2], 16) > 15 or int(i[3], 16) > 15 or int(i[4], 16) > 15:
                raise obd.InvalidDTC(i)

            #: Builds the first byte of the DTC and adds it to the list.
            dtc_first_hex = str(hex((dtc_type << 2) + int(i[1], 16)))[2:].upper()
            dtc_list.append(f'{dtc_first_hex}{i[2]}')

            #: Adds the second byte to the list.
            dtc_list.append(f'{i[3]}{i[4]}')

    #: Reverses the DTC list so the contents can be popped in the correct order (FILO)
    dtc_list.reverse()

    #: Each DTC is 2 bytes, or 2 elements in the list.
    num_dtcs = int(len(dtc_list) / 2)
    num_dtcs_byte = _convert_to_bytes(num_dtcs, 1)
    msg_bytes = _convert_to_bytes(len(dtc_list) + 2, 1)
    file_data = []

    #: Extra frames may be required.
    if num_dtcs >= 2:
        file_data.append(f'{frame_delay} {header_grp} 10 {msg_bytes} 43 {num_dtcs_byte} {dtc_list.pop()} '
                         f'{dtc_list.pop()} {dtc_list.pop()} {dtc_list.pop()}')

    #: No extra frames required. Only reachable if list contains exactly 1 DTC.
    else:
        file_data.append(f'{frame_delay} {header_grp} 10 {msg_bytes} 43 {num_dtcs_byte} {dtc_list.pop()} '
                         f'{dtc_list.pop()} 00 00')

    #: Number of extra frames needed in the group file.
    num_frames = int(num_dtcs / 3)

    #: Length of frame depends on CAN ID.
    if can_id == CAN_29:
        frame_length = 42
    else:
        frame_length = 36

    #: CAN frame number
    frame_num = 21

    #: Loops through the extra frames.
    while num_frames > 0:

        #: Current working frame
        current_frame = f'{frame_delay} {header_grp} {str(frame_num)} '

        #: Loops until all elements have been popped or current frame reaches its maximum length.
        while dtc_list:

            #: Current frame maximum length reached.
            if len(current_frame) > frame_length:
                break

            current_frame = current_frame + ' ' + dtc_list.pop()

        #: Pads the last frame with "00" bytes.
        while len(current_frame) < frame_length:
            current_frame += ' 00'

        #: Fixes spacing issue from padding.
        file_data.append(current_frame.replace('  ', ' '))
        num_frames -= 1
        frame_num += 1

    #: The group file is named based on the number of DTCs
    #: A randon number is added to the file name to ensure there are no duplicates.
    random_letter = random.choice(string.ascii_letters)
    can_id_str = f'CAN{str(can_id)}'
    file_name = f'{PATH}\\{can_id_str}\\DTCx{num_dtcs}_{random_letter}.grp'

    #: Creates the file path if it does not already exist.
    if not (os.path.exists(f'{PATH}\\{can_id_str}')):
        try:
            os.mkdir(f'{PATH}\\{can_id_str}')
        except OSError:
            raise

    #: Writes to the group file.
    with open(file_name, 'w') as f:
        for item in file_data:
            f.write(f'{item}\n')

    return f'{header_rx},Group,{file_name},False'


def _convert_to_bytes(data, num_bytes) -> str:
    """
    Converts an int or float to a string containing their hexadecimal conversion.
    
    @param data: The data that will be converted.
    @param num_bytes: The number of bytes the data will be encoded into.
    @return: A string containing the data in hexadecimal form with a space between each byte.
    """

    if isinstance(data, float):
        data = round(data)
    data = hex(data)[2:].zfill(num_bytes * 2).upper()
    data = ' '.join(data[i:i + 2] for i in range(0, len(data), 2))
    return data


def _write_file(file_data):
    """
    Creates the emulation file.

    @param file_data: All the generated CAN frames that will be written to the emulation file,
    along with their labels.

    @return: A boolean that is True if the file was successfully written, otherwise returns False.
    """

    #: The emulation file is named based on the CAN identifier.
    file_name = f'{PATH}\\{file_data[0]}\\{file_data[0]}_emulation.emu'

    #: Creates the file path if it does not already exist.
    if not (os.path.exists(f'{PATH}\\{file_data[0]}')):
        try:
            os.mkdir(f'{PATH}\\{file_data[0]}')
        except OSError:
            return False
    try:

        #: Writes all items to the file, excluding the CAN ID.
        with open(file_name, 'w') as f:
            for item in file_data:
                if item != 'CAN11' and item != 'CAN29':
                    f.write(f'{item}\n')
    except Exception:
        return False

    return True
