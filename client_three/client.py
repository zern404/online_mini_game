import socket
import time
import queue
from threading import Thread as t

IP, PORT = "localhost", 6000

command_queue = queue.Queue()
data_queue = queue.Queue()

class Client:
    def __init__(self, ip=IP, port=PORT):
        self.ip = ip
        self.port = port

        self.login_data = None

        self.s = None
        self._running = True
        self._tryconnect= True

        self.threads = []

    def send_msg(self, data):
        try:
            self.s.sendall(data.encode())
        except Exception as e:
            print(f"Error in send_msg: {e}")

    def stop_client(self):
        self.threads.clear()
        self._running = False
        self._tryconnect = False
        self.s = None

    def handle_server(self):
        print("Connected")
        try:
            while self._running:
                byte_data = self.s.recv(4096)
                
                if not byte_data:
                    break

                if byte_data:
                    decode_data = byte_data.decode()
                    if "cmd" in decode_data:
                        command_queue.put(decode_data.replace("cmd", "").strip())
                    else:
                        data_queue.put(decode_data)
                    print(decode_data)
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

                self.s = socket.socket()
                self.s.connect((self.ip, self.port))
                self.s.sendall(self.login_data)

                command_queue.put("connected")
            
                self.handle_server()    
            except Exception as e:
                print(f"Error in connect to server: {e}")
            finally:
                print("Try connect...")
                time.sleep(1)