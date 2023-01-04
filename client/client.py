import sys
import socket
import selectors
import traceback


sel = selectors.DefaultSelector()


import clientlib

def create_request(action, value, delay=0):
    if action == "press" or action=="release":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value),
        )
    if action == "push":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value, delay=delay),
        )
    else:
        return dict(
            type="binary/custom-client-binary-type",
            encoding="binary",
            content=bytes(action + value, encoding="utf-8")
        )

def start_connection(host, port, request):
    addr = (host, port)
    print(f"Starting connection to {addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = clientlib.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)


# if len(sys.argv) != 5 and len(sys.argv) != 6:
#     print(f"Usage: {sys.argv[0]} <host> <port> <action> <value> (<delay>)")
#     sys.exit()

# host = sys.argv[1]
# port = int(sys.argv[2])
# action = sys.argv[3]
# value = sys.argv[4]
# delay = 0

# if len(sys.argv) == 6:
#     delay = sys.argv[5]

"""
Read a file. For each line in file, action, value and delay will be separated by a space, then just perform each one sequentially.
"""
request = create_request(action, value, delay)
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