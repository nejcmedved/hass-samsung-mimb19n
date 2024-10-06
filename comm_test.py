import traceback
import os
from samsung_nasa.nasa import NasaParser, NasaPacket, NasaDevice
from cmd_shell import CmdShell
from samsung_nasa.nasa_task import NasaTask

from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    MIM_B19N_DEVICE = os.getenv("MIM_B19N_DEVICE")
    listen = NasaTask()
    listen.connect(MIM_B19N_DEVICE, 4660)
    listen.start()
    shell = CmdShell()

    while True:
        try:
            # siemens connection status
            cmd = shell.wait_input()
            if cmd is not None:
                try:
                    if cmd.startswith("i"):
                        chuncks = cmd.split(" ")
                        reg: int = 0
                        if len(chuncks) == 2:
                            reg = int(chuncks[1], 16)
                        packet = NasaPacket()
                        packet.dst_device = NasaDevice.Outdoor
                        # packet.add_read_msg(0x8204, 0, 2)
                        packet.add_read_msg(reg, 0, 2)
                        payload: bytearray = packet.encode()
                        print(f"send {' '.join(f'{byte:02X}' for byte in payload)}")
                        listen.sock.send(payload)

                        print(f"cmd {cmd}")
                    if cmd.startswith("w"):
                        packet = NasaPacket()
                        # packet.add_read_msg(0x8204, 0, 2)
                        packet.add_write_msg(0x4247, 400, 2)
                        payload: bytearray = packet.encode()
                        print(f"send {' '.join(f'{byte:02X}' for byte in payload)}")
                        listen.sock.send(payload)

                        print(f"cmd {cmd}")
                except Exception as e:
                    print(f"cmd exc {e}")
                    traceback.print_exc()
                    pass
        except KeyboardInterrupt:
            print("Exiting")
            exit(0)
