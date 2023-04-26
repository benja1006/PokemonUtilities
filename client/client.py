import sys
import socket
import selectors
import traceback
import argparse





import clientlib

def create_request(action, value, position):
    # if action == "press" or action=="release" or action=="tap":
    return dict(
        type="text/json",
        encoding="utf-8",
        content=dict(action=action, value=value, position=position),
    )
    # else:
    #     return dict(
    #         type="binary/custom-client-binary-type",
    #         encoding="binary",
    #         content=bytes(action + value, encoding="utf-8")
    #     )

def start_connection(host, port, request):
    addr = (host, port)
    print(f"Starting connection to {addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = clientlib.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)


async def main(action, value, position):
    host = '192.168.1.22'
    port = 12345
    sel = selectors.DefaultSelector()
    request = create_request(action, value, position)
    start_connection(host, port, request)


    try: 
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                    print(
                        f"Main: Error: Exception for {message.addr}:\n"
                        f"{traceback.format_exc()}"
                    )
                    message.close()
            # Check for a socket being monitored to continue
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', help='press, release or tap')
    parser.add_argument('value', help="button to be pressed")
    parser.add_argument('-p', '--position', help="position for stick commands", default='(2048,2048)')
    args = parser.parse_args()

    action = args.action.lower()
    value = args.value.lower()
    position = eval(args.position)
    