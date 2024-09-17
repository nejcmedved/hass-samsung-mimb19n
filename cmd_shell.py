import threading
import logging


class CmdShell(threading.Thread):
    def __init__(self):
        self.QuitEvent: threading.Event = threading.Event()
        threading.Thread.__init__(self)

    @staticmethod
    def do_l(line):  # logging
        efl2l = {logging.CRITICAL: 1, logging.ERROR: 2, logging.WARNING: 3, logging.INFO: 4, logging.DEBUG: 5,
                 logging.NOTSET: 99}
        l2efl = {v: k for k, v in efl2l.items()}
        ld = logging.root.manager.loggerDict
        loggers = [logging.getLogger(name) for name in ld]
        try:
            a = line.split(" ")
            if len(a) == 2:
                # set logging level
                for lg in loggers:
                    if a[0] in lg.name:
                        level: int = int(a[1])
                        if level == 0:
                            level = 1
                        lg.setLevel(l2efl[level])
                return
        except:
            pass
        # list all logging services
        for logger in loggers:
            efl = logger.getEffectiveLevel()
            print(f"{logger.name}")
            #print(f"{logger.name} : {efl2l[efl]}")

    def wait_input(self) -> str or None:
        user_input = input()
        cmd = user_input.strip('\n')
        if cmd.startswith("l"):
            self.do_l(cmd)
            return None
        print(f"->", end=" ")
        return cmd

    def run(self):
        while not self.QuitEvent.is_set():
            user_input = input()
            cmd = user_input.strip('\n')
            if cmd.startswith("l"):
                self.do_l(cmd)
            print(f"->", end=" ")


if __name__ == "__main__":
    shell: CmdShell = CmdShell()
    shell.start()
