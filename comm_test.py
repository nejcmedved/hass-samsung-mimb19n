import socket
import threading
import traceback

from samsung_nasa.nasa import NasaParser, NasaPacket
from cmd_shell import CmdShell
from samsung_nasa.nasa_task import NasaTask


if __name__ == '__main__':
    listen = NasaTask()
    listen.connect('192.168.1.46', 4660)
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
                        packet = NasaPacket()
                        # packet.add_read_msg(0x8204, 0, 2)
                        packet.add_read_msg(0x0407, 0, 2)
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
