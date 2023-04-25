import sys
import socket
import selectors
import traceback
import asyncio

# joycontrol imports
from joycontrol.memory import FlashMemory
from joycontrol.controller import Controller
from joycontrol import logging_default as log, utils
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.command_line_interface import ControllerCLI

sel = selectors.DefaultSelector()

import serverlib

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    message = serverlib.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <> <port>")
    sys.exit(1)


host, port = 'localhost', 12345
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print(f"listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# Controller specific things
spi_flash = FlashMemory()
controller = Controller.from_arg('PRO_CONTROLLER')
reconnect_bt_addr = "98:FE:94:4F:53:5B"
device_id = "98:FE:94:4F:53:5B"

class Emulator:
    async def setup(self):
        spi_flash = FlashMemory()
        controller = Controller.from_arg('PRO_CONTROLLER')
        print("Got Controller")
        with utils.get_output(path='log.txt', default=None) as capture_file:
            # prepare the the emulated controller
            factory = controller_protocol_factory(controller, spi_flash=spi_flash)
            ctl_psm, itr_psm = 17, 19
            transport, protocol = await create_hid_server(factory, reconnect_bt_addr=reconnect_bt_addr,
                                                        ctl_psm=ctl_psm,
                                                        itr_psm=itr_psm, capture_file=capture_file,
                                                        device_id=device_id)
            print("Made hid server")
            self.controller_state = protocol.get_controller_state()
            self.controller_state.connect()
            print("connected to controller")

            try:
                await self.run()
            finally:
                await transport.close()
    
    async def run(self):
        try: 
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            message.process_events(mask, emulator)
                        except Exception:
                            print(
                                f" Main: Error: Exception for {message.addr}:\n"
                                f"{traceback.format_exc()}"
                            )
                            message.close()

        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            sel.close()
    

    

emulator = Emulator()

loop = asyncio.get_event_loop()
loop.run_until_complete(
    emulator.setup()
)


# server stuff?
# try: 
#     while True:
#         events = sel.select(timeout=None)
#         for key, mask in events:
#             if key.data is None:
#                 accept_wrapper(key.fileobj)
#             else:
#                 message = key.data
#                 try:
#                     message.process_events(mask, emulator)
#                 except Exception:
#                     print(
#                         f" Main: Error: Exception for {message.addr}:\n"
#                         f"{traceback.format_exc()}"
#                     )
#                     message.close()

# except KeyboardInterrupt:
#     print("Caught keyboard interrupt, exiting")
# finally:
#     sel.close()