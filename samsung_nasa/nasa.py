import struct
import enum

NASA_REGISTERS = {
    0x4000: ("ENUM_IN_OPERATION_POWER", "Indoor unit power on/off"),
    0x4201: ("VAR_IN_TEMP_TARGET_F", "	variable waterOutSetTemp"),
    0x4247: ("VAR_IN_TEMP_WATER_OUTLET_TARGET_F", "Indoor unit set temperature"),
    0x8204: ("NASA_OUTDOOR_OUT_TEMP", "Outdoor temperature"),
    0x825E: ("NASA_OUTDOOR_WATER_TEMP", "Outdoor water temperature"),
    0x8411: ("NASA_OUTDOOR_CONTROL_WATTMETER_1UNIT",
             "Instantaneous power consumption of outdoor unit. One outdoor unit. Not used by the controller."),
    0x8413: ("LVAR_OUT_CONTROL_WATTMETER_1W_1MIN_SUM", "Outdoor unit instantaneous power consumption. Sum of modules"),
    0x0406: ("NASA_ALL_POWER_CONSUMPTION_SET", "	Total instantaneous power consumption"),
    0x0407: ("NASA_ALL_POWER_CONSUMPTION_CUMULATIVE", "	Total cumulative power consumption")
}

READ_REGISTERS = {
    0x8204: ("NASA_OUTDOOR_OUT_TEMP", "Outdoor temperature", None),
}

PACKET_NUMBER: int = 0


class NasaPacketType(enum.Enum):
    StandBy = 0
    Normal = 1
    Gathering = 2
    Install = 3
    Download = 4


class NasaDataType(enum.Enum):
    Undefined = 0
    Read = 1
    Write = 2
    Request = 3
    Notification = 4
    Response = 5
    Ack = 6
    Nack = 7


class NasaDevice(enum.Enum):
    Unknown = 0x00
    Outdoor = 0x10
    Indoor = 0x20


class NasaPacket:
    def __init__(self):
        self.packet_start = 0x32
        self.source_address = 0x0
        self.source_channel = 0x0
        self.dst_channel = 0x0
        self.dst_device: NasaDevice = NasaDevice.Unknown
        self.data: bytes = b''
        self.packet_information = False
        self.packet_type = NasaPacketType.Normal
        self.data_type = NasaDataType.Read
        self.num_messages = 0

    @staticmethod
    def crc16(data: bytearray, start_index: int, length: int):
        crc: int = 0
        for byte in data[start_index:start_index + length]:
            crc ^= byte << 8  # Move byte into the top 8 bits of crc
            for _ in range(8):
                if crc & 0x8000:  # If the leftmost (most significant) bit is 1
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF  # Trim CRC to 16 bits
        return crc

    def add_read_msg(self, register: int, value: int, payload_length: int):
        self.data += struct.pack(">H", register)
        if payload_length == 1:
            self.data += struct.pack("B", value)
        elif payload_length == 2:
            self.data += struct.pack(">H", value)
        elif payload_length == 4:
            self.data += struct.pack(">L", value)
        self.num_messages += 1

    def add_write_msg(self, register: int, value: int, payload_length: int):
        self.data_type = NasaDataType.Write
        self.data += struct.pack(">H", register)
        if payload_length == 1:
            self.data += struct.pack("B", value)
        elif payload_length == 2:
            self.data += struct.pack(">H", value)
        elif payload_length == 4:
            self.data += struct.pack(">L", value)
        else:
            raise ValueError(f"Invalid payload length: {payload_length}")
        self.num_messages += 1

    def encode(self):
        ret: bytearray = bytearray()
        ret += struct.pack("B", self.packet_start)
        ret.append(0x00)
        ret.append(0x00)
        # source
        ret.append(0xB0)  # we are wired remote
        ret.append(0x00)
        ret.append(0x00)
        # dest
        ret.append(self.dst_device.value)  # asking outdoor unit
        ret.append(0x00)
        ret.append(0x00)
        # packet info
        ret.append(192)  # TODO
        ret.append((self.packet_type.value << 4) + self.data_type.value)

        # packet number
        global PACKET_NUMBER
        ret.append(PACKET_NUMBER)
        PACKET_NUMBER += 1

        # messages
        ret.append(self.num_messages)
        ret += self.data

        ret_size = len(ret) + 1
        ret[1] = (ret_size >> 8)
        ret[2] = (ret_size & 0xFF)

        crc = self.crc16(ret, 3, ret_size - 4)
        ret.append(crc >> 8)
        ret.append(crc & 0xFF)

        ret.append(0x34)

        return ret


class NasaParser:
    def __init__(self):
        self.received_data = b''
        self.registers = {
            0x8204: None,
            0x4247: None,
            0x4000: None
        }
        pass

    def print_register(self, register: int, value):
        if register in NASA_REGISTERS.keys():
            print(f"Got register {NASA_REGISTERS[register][1]} value = {value}")
            self.registers[register] = value
        else:
            print(f"Got register={hex(register)} value={value}")

    def decode(self, data: bytes):
        print(f"data {' '.join(f'{byte:02X}' for byte in data)}")
        start, size, src_device = struct.unpack(">BHB", data[0:4])
        source_channel, source_address, dst_device, destination_channel, destination_address = struct.unpack(
            "BBBBB", data[4: 4 + 5])
        packet_info, data_type, packet_number = struct.unpack("BBB", data[9: 9 + 3])
        protocol_version = (packet_info & 96) >> 5
        data_type = int(data_type & 15)
        num_messages = data[12]

        # print(
        #     f"src_device={hex(src_device)} src_channel={(hex(source_channel))} dst_device={hex(dst_device)} dst_channel={(hex(destination_channel))} num_messages={num_messages} size = {size} data_len = {len(data)}")
        # print(
        #    f"packet_info={packet_info} data_type={data_type} packet_number={packet_number} protocol_version={protocol_version}")
        payload = data[12 + 1: -3]
        pos = 0
        for i in range(num_messages):
            dtype = (payload[pos] * 256) + payload[pos + 1]
            msg_num = dtype
            # print(f"msg_num {hex(msg_num)} ")
            dtype = (dtype & 1536) >> 9
            # print(f"msg_num {hex(msg_num)} dtype={dtype}")
            value = None
            if dtype == 0:
                value = payload[pos + 2]
                pos += 3
            elif dtype == 1:
                value = payload[pos + 2] << 8 | payload[pos + 3]
                pos += (2 + 2)
            elif dtype == 2:
                value = payload[pos + 2] << 24 | payload[pos + 3] << 16 | payload[pos + 4] << 8 | payload[pos + 5]
                pos += (2 + 4)
            elif dtype == 3:
                continue

            self.print_register(msg_num, value)
        end = data[-1]
        i = 4

    def process(self):
        pos = 0
        for char in self.received_data:
            if pos > len(self.received_data) - 16:
                # wont be enough for telegram anyway
                self.received_data = self.received_data[pos::]
                break
            # try to find some valid packets
            if char == 0x32:
                size = struct.unpack(">H", self.received_data[pos + 1:pos + 3])[0]
                if pos + 1 + size < len(self.received_data):
                    end = self.received_data[pos + 1 + size]
                    if end == 0x34:
                        self.decode(self.received_data[pos:pos + 2 + size])
                        self.received_data = self.received_data[pos + 2 + size:]
                a = 1
            pos += 1
        pass

    def feed(self, data: bytes):
        self.received_data += data
        self.process()
