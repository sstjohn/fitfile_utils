#!/usr/bin/env python3

"""subsport_tweak.py: change sub_sport fields in FIT files"""

__author__    = "Saul St. John"
__copyright__ = "Copyright 2021, Saul St. John"
__license__   = "GPLv3"
__version__   = "0.0.1"

import argparse
import struct
import sys

CRC_TABLE = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
		     0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]

# base type number: (endian ability, base field type, type name, invalid value, size, format string, comment)
FIT_BASE_TYPES = {
    0:	(0,	0x00,	"enum",	    0xFF,   	        1, "B",	""),
    1:	(0,	0x01,	"sint8",	0x7F,	            1, "b",	"2’s complement format"),
    2:	(0,	0x02,	"uint8",	0xFF,	            1, "B",	""),
    3:	(1,	0x83,	"sint16",	0x7FFF,	            2, "h",	"2’s complement format"),
    4:	(1,	0x84,	"uint16",	0xFFFF,	            2, "H",	""),
    5:	(1,	0x85,	"sint32",	0x7FFFFFFF,	        4, "i",	"2’s complement format"),
    6:	(1,	0x86,	"uint32",	0xFFFFFFFF,	        4, "I",	""),
    7:	(0,	0x07,	"string",	0x00,	            1, "s",	"Null terminated string encoded in UTF-8 format"),
    8:	(1,	0x88,	"float32",	0xFFFFFFFF,	        4, "f",	""),
    9:	(1,	0x89,	"float64",	0xFFFFFFFFFFFFFFFF,	8, "d",	""),
    10:	(0,	0x0A,	"uint8z",	0x00,	            1, "B",	""),
    11: (1,	0x8B,	"uint16z",	0x0000,	            2, "H",	""),
    12:	(1,	0x8C,	"uint32z",	0x00000000,	        4, "I",	""),
    13:	(0,	0x0D,	"byte",	    0xFF,	            1, "p",	"Array of bytes. Field is invalid if all bytes are invalid."),
    14:	(1,	0x8E,	"sint64",	0x7FFFFFFFFFFFFFFF,	8, "q",	"2’s complement format"),
    15:	(1,	0x8F,	"uint64",	0xFFFFFFFFFFFFFFFF,	8, "Q",	""),
    16:	(1,	0x90,	"uint64z",	0x0000000000000000,	8, "q",	""),
}

GLOBAL_MESSAGE_NUMBERS = {
    0:	    ("file_id", {0: "type", 1: "manufacturer", 2: "product", 3: "serial_number", 4: "time_created", 5: "number", 8: "product_name"}),
    1:	    ("capabilities", {}),
    2:  	("device_settings", {}),
    3:	    ("user_profile", {}),
    4:  	("hrm_profile", {}),
    5:	    ("sdm_profile", {}),
    6:  	("bike_profile", {}),
    7:  	("zones_target", {}),
    8:  	("hr_zone", {}),
    9:  	("power_zone", {}),
    10: 	("met_zone", {}),
    12: 	("sport", {0: "sport", 1: "sub_sport", 3: "name"}),
    15: 	("goal", {}),
    18: 	("session", {0: "event", 1: "event_type", 2: "start_time", 3: "start_position_lat", 4: "start_position_long", 5: "sport", 6: "sub_sport", 7: "total_elapsed_time", 8: "total_timer_time", 9: "total_distance", 253: "timestamp", 254: "message_index"}),
    19: 	("lap", {}),
    20: 	("record", {0: "position_lat", 1: "position_long", 2: "altitude", 3: "heart_rate", 4: "cadence", 5: "distance", 6: "speed", 7: "power", 8: "compressed_speed_distance", 9: "grade", 10: "resistance", 11: "time_from_course", 12: "cycle_length", 13: "temperature", 17: "speed_1s", 18: "cycles", 19: "total_cycles", 28: "compressed_accumulated_power", 29: "accumulated_power", 30: "left_right_balance", 31: "gps_accuracy", 32: "vertical_speed", 33: "calories", 39: "vertical_oscillation", 40: "stance_time_percent", 41: "stance_time", 42: "activity_type", 43: "left_torque_effectiveness", 44: "right_torque_effectiveness", 45: "left_pedal_smoothness", 46: "right_pedal_smoothness", 47: "combined_pedal_smoothness", 48: "time128", 49: "stroke_type", 50: "zone", 51: "ball_speed", 52: "cadence256", 53: "fractional_cadence", 54: "total_hemoglobin_conc", 55: "total_hemoglobin_conc_min", 56: "total_hemoglobin_conc_max", 57: "saturated_hemoglobin_percent", 58: "saturated_hemoglobin_percent_min", 59: "saturated_hemoglobin_percent_max", 62: "device_index", 67: "left_pco", 68: "right_pco", 69: "left_power_phase", 70: "left_power_phase_peak", 71: "right_power_phase", 72: "right_power_phase_peak", 73: "enhanced_speed", 78: "enhanced_altitude", 81: "battery_soc", 82: "motor_power", 83: "vertical_ratio", 84: "stance_time_balance", 85: "step_length", 91: "absolute_pressure", 92: "depth", 93: "next_stop_depth", 94: "next_stop_time", 95: "time_to_surface", 96: "ndl_time", 97: "cns_load", 98: "n2_load", 114: "grit", 115: "flow", 117: "ebike_travel_range", 118: "ebike_battery_level", 119: "ebike_assist_mode", 120: "ebike_assist_level_percent", 139: "core_temperature", 253: "timestamp"}),
    21: 	("event", {0: "event", 1: "event_type", 2: "data16", 3: "data", 4: "event_group", 7: "score", 8: "opponent_score", 9: "front_gear_num", 10: "front_gear", 11: "rear_gear_num", 12: "rear_gear", 13: "device_index", 21: "radar_threat_level_max", 22: "radar_threat_count"}),
    23: 	("device_info", {}),
    26: 	("workout", {}),
    27: 	("workout_step", {}),
    28: 	("schedule", {}),
    30: 	("weight_scale", {}),
    31: 	("course", {}),
    32: 	("course_point", {}),
    33: 	("totals", {}),
    34: 	("activity", {}),
    35: 	("software", {}),
    37: 	("file_capabilities", {}),
    38: 	("mesg_capabilities", {}),
    39: 	("field_capabilities", {}),
    49: 	("file_creator", {0: "software_version", 1: "hardware_version"}),
    51: 	("blood_pressure", {}),
    53: 	("speed_zone", {}),
    55: 	("monitoring", {}),
    72: 	("training_file", {}),
    78: 	("hrv", {0: "time"}),
    80: 	("ant_rx", {}),
    81: 	("ant_tx", {}),
    82: 	("ant_channel_id", {}),
    101:	("length", {}),
    103:	("monitoring_info", {}),
    105:	("pad", {}),
    106:	("slave_device", {}),
    127:	("connectivity", {}),
    128:	("weather_conditions", {}),
    129:	("weather_alert", {}),
    131:	("cadence_zone", {}),
    132:	("hr", {}),
    142:	("segment_lap", {}),
    145:	("memo_glob", {}),
    148:	("segment_id", {}),
    149:	("segment_leaderboard_entry", {}),
    150:	("segment_point", {}),
    151:	("segment_file", {}),
    158:	("workout_session", {}),
    159:	("watchface_settings", {}),
    160:	("gps_metadata", {}),
    161:	("camera_event", {}),
    162:	("timestamp_correlation", {}),
    164:	("gyroscope_data", {}),
    165:	("accelerometer_data", {}),
    167:	("three_d_sensor_calibration", {}),
    169:	("video_frame", {}),
    174:	("obdii_data", {}),
    177:	("nmea_sentence", {}),
    178:	("aviation_attitude", {}),
    184:	("video", {}),
    185:	("video_title", {}),
    186:	("video_description", {}),
    187:	("video_clip", {}),
    188:	("ohr_settings", {}),
    200:	("exd_screen_configuration", {}),
    201:	("exd_data_field_configuration", {}),
    202:	("exd_data_concept_configuration", {}),
    206:	("field_description", {}),
    207:	("developer_data_id", {}),
    208:	("magnetometer_data", {}),
    209:	("barometer_data", {}),
    210:	("one_d_sensor_calibration", {}),
    225:	("set", {}),
    227:	("stress_level", {}),
    258:	("dive_settings", {}),
    259:	("dive_gas", {}),
    262:	("dive_alarm", {}),
    264:	("exercise_title", {}),
    268:	("dive_summary", {}),
    285:	("jump", {}),
    317:	("climb_pro", {}),
    0xFF00:	("mfg_range_min", {}),
    0xFFFE:	("mfg_range_max", {}),
}

def parse_file_header(data):
    header_size = struct.unpack_from("B", data)[0]
    if header_size == 12:
        protocol_version, profile_version, data_size, data_type = struct.unpack_from("<BHI4s", data, 1)
        header_crc = 0
    else:
        protocol_version, profile_version, data_size, data_type, header_crc = struct.unpack_from("<BHI4sH", data, 1)
    return header_size, protocol_version, profile_version, data_size, data_type, header_crc
    

def do_crc(data, start, end):
	crc = 0
	for b in data[start:end]:
		tmp = CRC_TABLE[crc & 0xf]
		crc = (crc >> 4) & 0x0fff
		crc = crc ^ tmp ^ CRC_TABLE[b & 0xf]
		tmp = CRC_TABLE[crc & 0xf]
		crc = (crc >> 4) & 0x0fff
		crc = crc ^ tmp ^ CRC_TABLE[(b >> 4) & 0xf]
	return crc
    

def parse_record_header_byte(b):
    compressed_header =         (b & 0b10000000) >> 7
    if not compressed_header:
        definition_message =          (b & 0b1000000)  >> 6
        message_type_specific = (b & 0b100000)   >> 5
        reserved =              (b & 0b10000)    >> 4
        local_message_type =     b & 0b1111
        time_offset = 0
    else:
        definition_message = 0
        message_type_specific = 0
        reserved = 0
        local_message_type = (b & 0b01100000) >> 5
        time_offset = b & 0b11111
    return compressed_header, definition_message, message_type_specific, local_message_type, time_offset


def parse_definition_record(local_message_type, developer_data_flag, data, ptr):
    reserved, architecture, global_message_number, field_count = struct.unpack_from("<BBHB", data, ptr)
    if reserved:
        print("reserved bit set in definition record")
    fields = []
    developer_field_count = 0
    developer_fields = []
    ptr += 5
    for i in range(field_count):
        field_definition_number, field_size, base_type = struct.unpack_from("<BBB", data, ptr)
        ptr += 3
        fields.append((field_definition_number, field_size, parse_base_type(base_type)))       
    if developer_data_flag:
        developer_field_count = struct.unpack_from("<c", data, ptr)
        ptr += 1
        for i in range(developer_field_count):
            field_number, size, developer_data_index = struct.unpack_from("<BBB", data, ptr)
            ptr += 3
            developer_data_fields.append((field_number, size, developer_data_index))            
    return architecture, global_message_number, field_count, fields, developer_field_count, developer_fields, ptr


def parse_base_type(b):
    endian =           (b & 0b10000000) >> 7
    reserved =         (b & 0b01100000) >> 5
    base_type_number = (b & 0b00011111)
    if reserved:
        print("reserved bits set in base type %d" % b)
    return (endian, base_type_number)
    
def main(args):
    
    parser = argparse.ArgumentParser(description="change sub_sport fields in FIT files")
    parser.add_argument("-f", "--from", type=int, default=6, help="subsport to change from", dest="subsport_from")
    parser.add_argument("-t", "--to", type=int, default=58, help="subsport to change to", dest="subsport_to")
    parser.add_argument("infile", type=argparse.FileType("rb"), help="input FIT file")
    parser.add_argument("outfile", type=argparse.FileType("wb"), help="output FIT file")
    args = parser.parse_args()
    
    print("processing %s" % args.infile.name)
    data = bytearray(args.infile.read())
    args.infile.close()

    header_size, protocol_version, profile_version, data_size, data_type, header_crc = parse_file_header(data)
    ptr = header_size

    if header_crc:
        if not do_crc(data, 0, 12) == header_crc:
            print("header crc bad")
        else:
            print("header crc good")

    if not do_crc(data, header_size, len(data)):
        print("file crc good")
    else:
        print("file crc bad")

    data_dirty = False
    local_message_types = {}
    while ptr < data_size + header_size:
        compressed_header, definition_message, message_type_specific, local_message_type, time_offset = parse_record_header_byte(data[ptr])
        ptr += 1
        
        if definition_message:
            architecture, global_message_number, field_count, fields, developer_field_count, developer_fields, ptr = parse_definition_record(local_message_type, message_type_specific, data, ptr)
            local_message_types[local_message_type] = (architecture, global_message_number, field_count, fields, developer_field_count, developer_fields)
        else:
            architecture, global_message_number, field_count, fields, developer_field_count, developer_fields = local_message_types[local_message_type]
            try:
                global_message_type = GLOBAL_MESSAGE_NUMBERS[global_message_number]
            except KeyError:
                global_message_type = ("unknown (%d)" % global_message_number, {})
                
            for field in fields:
                field_definition_number, field_size, (endian, base_type_number) = field
                try:
                    field_definition_type = global_message_type[1][field_definition_number]
                except:
                    field_definition_type = "unknown %d" % field_definition_number
                    
                base_type = FIT_BASE_TYPES[base_type_number]
                endian_ability, base_field_type, type_name, invalid_value, type_size, format_character, comment = base_type
                
                format_character_count = field_size / type_size
                
                field_data = struct.unpack("<%d%s" % (format_character_count, format_character), data[ptr:ptr+field_size])[0]
                
                
                if field_definition_type == "sub_sport":
                    if field_data == args.subsport_from:
                        print("found subsport %d in %s message, changing to subsport %d" % (args.subsport_from, global_message_type[0], args.subsport_to))
                        new_field_data = struct.pack("<%d%s" % (format_character_count, format_character), args.subsport_to)
                        data[ptr:ptr+field_size] = new_field_data
                        data_dirty = True
                
                ptr += field_size

    if not data_dirty:
        print("indoor cycling subsport not found, aborting")
        return

    new_crc = struct.pack("<H", do_crc(data, header_size, len(data) - 2))
    data[-2:] = new_crc

    args.outfile.write(data)
    args.outfile.close()

    print("modified file written to %s" % args.outfile.name)

if __name__ == "__main__":
    main(sys.argv)
