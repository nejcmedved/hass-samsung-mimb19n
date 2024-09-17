import threading
import socket
import time
from .nasa import NasaParser


class NasaTask(threading.Thread):
    def __init__(self, sock=None):
        super().__init__()
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.telegram: bytes = b''
        self.daemon = True
        self.quit_event = threading.Event()
        self.lock = threading.Lock()
        self.parser = NasaParser()

    def connect(self, host, port):
        try:
            self.sock.connect((host, port))
            # self.sock.settimeout(0)
            self.sock.setblocking(False)
            print('Successful Connection')
        except:
            print('Connection Failed')

    def send_data(self, data: bytearray | bytes):
        with self.lock:
            self.sock.sendall(data)

    def read_data(self, length):
        try:
            data = self.sock.recv(length)
            self.parser.feed(data)
        except TimeoutError:
            # no data
            pass
        except BlockingIOError:
            # no data
            pass
        return

    def run(self):
        """ continously read data from samsung"""
        while not self.quit_event.is_set():
            with self.lock:
                self.read_data(64)
            time.sleep(0.1)
