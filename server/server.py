import sys
import socket
import selectors
import traceback
import asyncio
import argparse

# joycontrol imports
from joycontrol.memory import FlashMemory
from joycontrol.controller import Controller
from joycontrol import logging_default as log, utils
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.command_line_interface import ControllerCLI



sel = selectors.DefaultSelector()

import serverlib

def accept_wrapper(sock, emulator):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    message = serverlib.Message(sel, conn, addr, emulator)
    sel.register(conn, selectors.EVENT_READ, data=message)



def setup_server(args):
    host = '192.168.1.22'
    port = args.port
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
#reconnect_bt_addr = "98:FE:94:4F:53:5B"
#device_id = "98:FE:94:4F:53:5B"

class Emulator:
    async def setup(self):
        spi_flash = FlashMemory()
        controller = Controller.from_arg('PRO_CONTROLLER')
        print("Got Controller")
        with utils.get_output(path='log.txt', default=None) as capture_file:
            # prepare the the emulated controller
            factory = controller_protocol_factory(controller, spi_flash=spi_flash, reconnect=args.reconnect_bt_addr)
            ctl_psm, itr_psm = 17, 19
            transport, protocol = await create_hid_server(factory, reconnect_bt_addr=args.reconnect_bt_addr,
                                                        ctl_psm=ctl_psm,
                                                        itr_psm=itr_psm, capture_file=capture_file,
                                                        device_id=args.device_id)
            print("Made hid server")
            self.controller_state = protocol.get_controller_state()
            # self.controller_state.connect()
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
                        accept_wrapper(key.fileobj, self)
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
    
    def press_button(self, button):
        print('pressing button', button)

    def release_buton(self, button):
        print('releasing button', button)

    def tap_button(self, button, delay):
        print('Tapping button', button, 'for', delay, 'seconds')
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('controller', help='JOYCON_R, JOYCON_L or PRO_CONTROLLER')
    parser.add_argument('-l', '--log', help="BT-communication logfile output")
    parser.add_argument('-d', '--device_id', help='not fully working yet, the BT-adapter to use')
    parser.add_argument('--spi_flash', help="controller SPI-memory dump to use")
    parser.add_argument('-r', '--reconnect_bt_addr', type=str, default=None,
                        help='The Switch console Bluetooth address (or "auto" for automatic detection), for reconnecting as an already paired controller.')
    parser.add_argument('--nfc', type=str, default=None, help="amiibo dump placed on the controller. Äquivalent to the nfc command.")
    parser.add_argument('-p', '--port', type=int, default=12345, help="The port to run the server on.")
    args = parser.parse_args()
    
    setup_server(args)
    emulator = Emulator()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        emulator.setup()
    )


