from __future__ import annotations
import logging
import time
import os
from paho.mqtt import client as mqtt_client
import json
import signal
from mqtt_config import MQTT_CONFIG
from dotenv import load_dotenv
from samsung_nasa.nasa_task import NasaTask
from samsung_nasa.nasa import NasaPacket, NasaDevice

MIM_B19N_DEVICE: str | None = None
MQTT_BROKER: str | None = None
MQTT_USERNAME: str | None = None
MQTT_PASSWORD: str | None = None

state_topic = 'mimb19n/alive/state'
delay = 5


def interpret_signed_16(value: int):
    if value & 0x8000:
        return value - 0x10000
    return value

def main():
    load_dotenv()

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

    # Send messages in a loop
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, "hass-samsung")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    # client.will_set()
    client.connect(MQTT_BROKER)
    client.loop_start()

    # prepare nasa parser
    nasa_task = NasaTask()
    nasa_task.connect(MIM_B19N_DEVICE, 4660)
    nasa_task.start()

    def on_message(client, userdata, message):
        print("Received message '" + str(message.payload) + "' on topic '"
              + message.topic + "' with QoS " + str(message.qos))
        if message.topic == "homeassistant/radiators_set_temperature/set":
            value = int(float(message.payload) * 10)
            packet = NasaPacket()
            packet.dst_device = NasaDevice.Indoor
            packet.add_write_msg(0x4247, value, 2)
            payload: bytearray = packet.encode()
            print(f"send {' '.join(f'{byte:02X}' for byte in payload)}")
            nasa_task.send_data(payload)
            logger.info(f"set new temperature for radiators to {value}")

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    client.on_message = on_message
    client.subscribe("homeassistant/+/set")

    # publish config to hass
    for key, val in MQTT_CONFIG.items():
        client.publish(key, json.dumps(val))

    logger.info(f"Mqtt connected")

    while True:
        # house heating
        try:
            packet = NasaPacket()
            packet.dst_device = NasaDevice.Outdoor
            packet.add_read_msg(0x8204, 0, 2)
            payload: bytearray = packet.encode()
            print(f"send {' '.join(f'{byte:02X}' for byte in payload)}")
            nasa_task.send_data(payload)

            packet = NasaPacket()
            packet.dst_device = NasaDevice.Indoor
            packet.add_read_msg(0x4247, 0, 2)
            packet.add_read_msg(0x4000, 0, 1)
            payload: bytearray = packet.encode()
            print(f"send {' '.join(f'{byte:02X}' for byte in payload)}")
            nasa_task.send_data(payload)

            # publish to hass
            if nasa_task.parser.registers[0x8204] is not None:
                client.publish("homeassistant/outdoor_temperature/state",
                               nasa_task.parser.registers[0x8204] / 10)

            if nasa_task.parser.registers[0x4247] is not None:
                client.publish("homeassistant/radiators_current_temperature/state",
                               nasa_task.parser.registers[0x4247] / 10)

            if nasa_task.parser.registers[0x4000] is not None:
                payload: str = "heat" if nasa_task.parser.registers[0x4000] == 1 else "off"
                client.publish("homeassistant/radiators_mode/state", payload)

            time.sleep(delay)
        except Exception as e:
            logger.error(f"Exception {e}")
            time.sleep(1)
            exit(0)
        except KeyboardInterrupt:
            logger.info(f"Stopping")
            exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('hass_mimb19n')
    logger.info(f"Starting...")
    main()

