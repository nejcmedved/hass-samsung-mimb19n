from __future__ import annotations

import logging
import time
import os
import paho.mqtt.client as mqtt
import pymodbus
from pymodbus.client import ModbusTcpClient
import json
import signal

MIM_B19N_DEVICE: str | None = None
MQTT_BROKER: str | None = None
MQTT_USERNAME: str | None = None
MQTT_PASSWORD: str | None = None

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
    "homeassistant/climate/radiators/config": {
        "device_class": "climate",
        # "temperature_state_topic": "homeassistant/radiators_set_temperature/state",
        "current_temperature_topic": "homeassistant/radiators_current_temperature/state",
        "temperature_command_topic": "homeassistant/radiators_set_temperature/set",
        "mode_state_topic": "homeassistant/radiators_mode/state",
        "mode_command_topic": "homeassistant/radiators_mode/set",
        "unique_id": "samsungmimb19n_radiators",
        "max_temp": 55.0,
        "min_temp": 35.0,
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Radiators temperature control",
        "modes": ["off", "heat"],
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
    },
    "homeassistant/sensor/compressor_frequency/config": {
        "unit_of_measurement": "Hz",
        "state_topic": "homeassistant/compressor_frequency/state",
        "unique_id": "samsungmimb19n_compressor_frequency",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Compressor Frequency",
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
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")

    if MQTT_BROKER is None:
        logger.error("define Mqtt broker ip to MQTT_BROKER environment variable")
        exit(-1)

    if MIM_B19N_DEVICE is None:
        logger.error("define mimb19n device ip to MIM_B19N_DEVICE environment variable")
        exit(-1)

    if MQTT_PASSWORD is None or MQTT_USERNAME is None:
        logger.error("define MQTT_PASSWORD and MQTT_USERNAME")
        exit(-1)

    modbus = ModbusTcpClient(host=MIM_B19N_DEVICE, port=4660, framer=pymodbus.Framer.RTU, timeout=5)
    modbus.connect()
    modbus.write_registers(address=6000, values=[0x8238, 0x8276, 0x8204], slave=2)
    modbus.write_registers(address=7000, values=[0x4087, 0x42f1, 0x4067], slave=2)
    # Send messages in a loop
    client = mqtt.Client("hass-mimb19n")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    # client.will_set()
    client.connect(MQTT_BROKER)
    client.loop_start()


    def on_message(client, userdata, message):
        print("Received message '" + str(message.payload) + "' on topic '"
              + message.topic + "' with QoS " + str(message.qos))
        if message.topic == "homeassistant/radiators_set_temperature/set":
            reg = 69
            value = int(float(message.payload) * 10)
            a = modbus.write_register(reg, value, 2)
            logger.info(f"set new temperature for radiators to {value}")


    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        exit(0)


    signal.signal(signal.SIGINT, signal_handler)

    client.on_message = on_message
    client.subscribe("homeassistant/+/set")

    for key, val in MQTT_CONFIG.items():
        client.publish(key, json.dumps(val))

    logger.info(f"Mqtt connected")

    while True:
        # house heating
        try:
            result = modbus.read_holding_registers(50, 1, 2)
            ok = result.registers[0]
            result = modbus.read_holding_registers(52, 1, 2)
            logger.info(f"House heading is operating {bool(result.registers[0])}")
            payload = "heat" if result.registers[0] == 1 else "off"
            client.publish("homeassistant/radiators_mode/state", payload)
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
            logger.info(f"Water in temperature {result.registers[0] / 10} C")  # 65
            logger.info(f"Water out temperature {result.registers[1] / 10} C")  # 66
            radiators_current_temperature = result.registers[3] / 10
            logger.info(f"Heating water set temperature {radiators_current_temperature} C")  # 68
            client.publish("homeassistant/radiators_current_temperature/state", radiators_current_temperature)

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
            client.publish("homeassistant/compressor_frequency/state", result.registers[0])
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
        except KeyboardInterrupt:
            logger.info(f"Stopping")
            exit(0)
