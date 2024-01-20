from __future__ import annotations

import logging
import time
import os
import paho.mqtt.client as mqtt
import pymodbus
from pymodbus.client import ModbusTcpClient
import json

MIM_B19N_DEVICE: str | None = None
MQTT_BROKER: str | None = None

# broker = '192.168.1.204'
state_topic = 'mimb19n/alive/state'
delay = 5

# Send a single message to set the mood
MQTT_CONFIG = {
    "homeassistant/climate/dhw/config": {
        "device_class": "climate",
        "temperature_state_topic": "homeassistant/dhw_set_temperature/state",
        "current_temperature_topic ": "homeassistant/dhw_current_temperature/state",
        "mode_state_topic": "homeassistant/dhw_mode/state",
        "mode_command_topic": "homeassistant/dhw_mode/set",
        "preset_mode_state_topic": "homeassistant/dhw_preset_mode/state",
        "preset_mode_command_topic": "homeassistant/dhw_preset_mode/set",
        "unique_id": "samsungmimb19n_dhw",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Hot water",
        "modes": ["off", "heat"],
        "preset_modes": ["Eco", "Normal", "Boost"]
    },
    "homeassistant/sensor/outdoor_temperature/config": {
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_topic": "homeassistant/outdoor_temperature/state",
        "unique_id": "samsungmimb19n_dhw",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Outdoor Temperature",
    }
}


def interpret_signed_16(value: int):
    if value & 0x8000:
        return value - 0x10000
    return value


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('hass_mimb19n')
    logger.info(f"Starting...")

    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MIM_B19N_DEVICE = os.getenv("MIM_B19N_DEVICE")

    modbus = ModbusTcpClient(host=MIM_B19N_DEVICE, port=4660, framer=pymodbus.Framer.RTU, timeout=5)
    modbus.connect()
    modbus.write_registers(address=6000, values=[0x8238, 0x8276, 0x8204], slave=2)
    modbus.write_registers(address=7000, values=[0x4087, 0x42f1, 0x4067], slave=2)
    # Send messages in a loop
    client = mqtt.Client("hass-mimb19n")
    client.username_pw_set('nejcmedved', 'nejcmedved')
    # client.will_set()
    client.connect(MQTT_BROKER)
    client.loop_start()

    def on_message(client, userdata, message):
        print("Received message '" + str(message.payload) + "' on topic '"
              + message.topic + "' with QoS " + str(message.qos))


    client.on_message = on_message
    client.subscribe("homeassistant/+/set")

    for key, val in MQTT_CONFIG.items():
        client.publish(key, json.dumps(val))

    logger.info(f"Mqtt connected")

    while True:
        # house heating
        try:
            result = modbus.read_holding_registers(52, 1, 2)
            logger.info(f"House heading is operating {bool(result.registers[0])}")
            # house heating mode
            result = modbus.read_holding_registers(53, 1, 2)
            modes = {
                0: 'Water law',
                4: 'Heating',
                1: 'Cooling'
            }
            logger.info(f"House heading is operating in mode {modes[result.registers[0]]}")
            # water in / out / set
            result = modbus.read_holding_registers(65, 4, 2)
            logger.info(f"Water in temperature {result.registers[0] / 10} C")
            logger.info(f"Water out temperature {result.registers[1] / 10} C")
            logger.info(f"Heating water set temperature {result.registers[3] / 10} C")

            # dhw
            result = modbus.read_holding_registers(72, 4, 2)
            logger.info(f"DHW on {result.registers[0]}")
            payload = "heat" if result.registers[0] == 1 else "off"
            client.publish("homeassistant/dhw_mode/state", payload)

            logger.info(f"DHW mode {result.registers[1]}")
            dhw_mode_num: int = result.registers[1]
            dhw_mode_str: str = ""
            if dhw_mode_num == 0:
                dhw_mode_str = "Eco"
            elif dhw_mode_num == 1:
                dhw_mode_str = "Normal"
            elif dhw_mode_num == 2:
                dhw_mode_str = "Boost"
            client.publish("homeassistant/dhw_preset_mode/state", dhw_mode_str)
            dhw_set_temperature: float = result.registers[2] / 10
            logger.info(f"DHW set temperature {result.registers[2] / 10} C")
            client.publish("homeassistant/dhw_set_temperature/state", dhw_set_temperature)
            # dhw current temp
            dhw_current_temperature: float = result.registers[3] / 10
            client.publish("homeassistant/dhw_current_temperature/state", dhw_current_temperature)
            logger.info(f"DHW current temperature {result.registers[3] / 10} C")

            # extended registers
            result = modbus.read_holding_registers(4, 3, 2)
            logger.info(f"Compressor 1 freq {result.registers[0]} Hz")
            logger.info(f"Compressor 2 freq {result.registers[1]} Hz")
            outdoor_temperature = interpret_signed_16(result.registers[2]) / 10
            logger.info(f"Outdoor temperature {outdoor_temperature} C")
            client.publish("homeassistant/outdoor_temperature/state",
                           outdoor_temperature)

            # extended registers 2
            result = modbus.read_holding_registers(82, 3, 2)
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Exception {e}")
            time.sleep(1)
            exit(0)
