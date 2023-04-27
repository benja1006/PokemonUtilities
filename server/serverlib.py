import sys
import selectors
import json
import io
import struct
import asyncio
import logging



class Message:
    def __init__(self, selector, sock, addr, emulator):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False
        self.emulator = emulator

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {mode!r}.")
        self.selector.modify(self.sock, events, data=self)
    
    async def process_events(self, mask) -> None:
        if mask & selectors.EVENT_READ:
            logging.debug("reading")
            self.read()
        if mask & selectors.EVENT_WRITE:
            logging.debug("writing")
            await self.write()

    def preprocess_protoheader(self) -> None:
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]
    
    def process_jsonheader(self) -> None:
        logging.debug("processing jsonheader")
        hdrlen = self._jsonheader_len
        logging.debug(len(self._recv_buffer))
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not  in self.jsonheader:
                    raise ValueError(f"Missing required header '{reqhdr}'.")
    
    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            logging.info(f"Received request {self.request!r} from {self.addr}")
        else:
            self.request = data
            logging.info(
                f"Received {self.jsonheader['content-type']} "
                f"request from {self.addr}"
            )
        self._set_selector_events_mask("w")

    async def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = await self._create_response_json_content()
        else:
            # Binary or unknown content type
            response = self._create_response_binary_content()
        message = self._create_message(**response)
        self.response_created = True
        self._send_buffer += message
    
    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")
    
    def _write(self):
        if self._send_buffer:
            logging.debug(f"Sending {self._send_buffer}")
            try:
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                #Resource temporarily unavailable
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                if sent and not self._send_buffer:
                    self.close()    
    def read(self) -> None:
        self._read()
        if self._jsonheader_len is None:
            self.preprocess_protoheader()

        
        if self._jsonheader_len is not None:
            logging.debug(f"The header is {self._jsonheader_len} bytes long")
            if self.jsonheader is None:
                self.process_jsonheader()
        
        if self.jsonheader:
            logging.debug(f"The json header is {self.jsonheader}")
            if self.request is None:
                self.process_request()

    async def write(self) -> None:
        if self.request:
            if not self.response_created:
                await self.create_response()
        self._write()
    
    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj
    
    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    async def _create_response_json_content(self):
        action = self.request.get("action")
        print(action, "-ing")
        if action == "press":
            btn = self.request.get("value")
            await self.emulator.press_button(btn)
            content = {"success": True}
        elif action == "release":
            btn = self.request.get("value")
            await self.emulator.release_button(btn)
            content = {"success": True}
        elif action == "tap":
            btn = self.request.get("value")
            await self.emulator.tap_button(btn)
            content = {"success": True}
        elif action == "stick_hold":
            stick = self.request.get("value")
            position = self.request.get("position")
            self.emulator.stick_hold(stick, position)
            content = {"success": True}
        elif action == "stick_flick":
            stick = self.request.get("value")
            position = self.request.get("position")
            self.emulator.stick_flick(stick, position)
            content = {"success": True}
        elif action == "stick_reset":
            stick = self.request.get("value")
            self.emulator.stick_reset(stick)
            content = {"success": True}
        else:
            content = {"result": f"Error: invalid action '{action}'."}
         
        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response

    def _create_response_binary_content(self):
        response = {
            "content_bytes": b"First 10 bytes of request: "
            + self.request[:10],
            "content_type": "binary/custom-server-binary-type",
            "content_encoding": "binary",
        }
        return response

    def close(self):
        logging.info(f"Closing connection to {self.addr}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            logging.error(
                f"Error: selector.unregister() exception for "
                f"{self.addr}: {e!r}"
            )

        try:
            self.sock.close()
        except OSError as e:
            logging.error(f"Error: socket.close() exception for {self.addr}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

