import socket
import time
import queue
import json
from functools import wraps
from threading import Thread as t

IP, PORT = "est-bits.gl.at.ply.gg", 3636

interface_queue = queue.Queue()
game_command_queue = queue.Queue()
command_queue = queue.Queue()
data_queue = queue.Queue()
ping_queue = queue.Queue()

class Client:
    def __init__(self, ip=IP, port=PORT):
        self.ip = ip
        self.port = port

        self.login_data = None

        self.s = None
        self._running = True
        self._tryconnect= True

        self.threads = []

        self._json_buffer = ""

    def __new_thread(self, func, *args, **kwargs):
        thread = t(target=func, args=args, kwargs=kwargs, daemon=True)
        self.threads.append(thread)
        thread.start()
    
    def __kill_threads(self):
        for thread in self.threads:
            if thread.is_alive():
                if not thread.daemon:
                    thread.join(timeout=2)  
        self.threads.clear()

    def ping_timer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            ping = int((time.time() - start) * 1000)
            if result:
                print(f"Ping: {ping} ms")
                return ping
            else:
                return None
        return wrapper

    @ping_timer
    def ping(self):
        self.send_msg("ping")
        try:
            pong = ping_queue.get(timeout=3)
            if pong == "pong":
                return True
        except Exception as e:
            print(f"Ping error: {e}")
        return False

    def send_msg(self, data, _json=False):
        try:
            if _json:
                json_byte_data = json.dumps(data) + "\n"
                self.s.sendall(json_byte_data.encode())
            else:
                self.s.sendall(data.encode())
        except Exception as e:
            print(f"Error in send_msg: {e}")

    def stop_client(self):
        self.__kill_threads()
        self._running = False
        self._tryconnect = False
        self.s = None

    def handle_server(self):
        try:
            while self._running:
                byte_data = self.s.recv(4096)
                
                if not byte_data:
                    break

                if byte_data:
                    decode_data = byte_data.decode()
                    if "cmd" in decode_data:
                        command_queue.put(decode_data.replace("cmd", "").strip())
                    elif "connected" in decode_data:
                        command_queue.put("connected")
                    elif "pong" in decode_data:
                        ping_queue.put("pong")
                    elif "room found!" in decode_data:
                        command_queue.put(decode_data)
                        self.send_msg("ready")
                    elif "restart" in decode_data:
                        interface_queue.put("restart")
                    elif "start game" in decode_data:
                        command_queue.put(decode_data)
                    elif "room closed" in decode_data:
                        game_command_queue.put(decode_data)
                    else:
                        self._json_buffer += decode_data
                        while "\n" in self._json_buffer:
                            line, self._json_buffer = self._json_buffer.split("\n", 1)
                            line = line.strip()
                            if line:
                                try:
                                    data_queue.put(json.loads(line))
                                except Exception as e:
                                    print(f"decode error: {e} | line: {line!r}")
                        
        except Exception as e:
            print(f"Error in handle server: {e}")
        finally:
            print("Connection lost.")
            command_queue.put("disconnected")

    def connect_server(self, login_data=None):
        if login_data:
            self.login_data = login_data
        while self._tryconnect:
            try:
                if self.s:
                    self.s.close()
                self.s = None

                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((self.ip, self.port))
                self.s.sendall(self.login_data)
            
                self.handle_server()    
            except Exception as e:
                print(f"Error in connect to server: {e}")
            finally:
                print("Try connect...")
                time.sleep(1)