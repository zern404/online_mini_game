import socket 
from threading import Thread as t
import logging as logs
import queue as q
import colorama
import time
import json 

IP, PORT = "localhost", 7000
LOGIN_DATA = {
    "login": "admin",
    "password": "admin",
    "public_key": "ggvp"
}


class Client:
    def __init__(self, ip, port):
        self.ip = ip 
        self.port = port 

        self.threads = []
        self.login_data_json = json.dumps(LOGIN_DATA)

        self.sock = None
        self.queue = q.Queue()

        self.try_conn = True 
        self.listen = True

    def stop(self):
        logs.warning("Client close!")
        self.try_conn = False
        self.listen = False
        self.threads.clear()

    def connect(self) -> bool:
        self.sock = None
        while self.try_conn:
            try:

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
                    self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    self.sock.connect((self.ip, self.port))
                    
                    logs.info("Sending user-data to sign")
                    self.sock.sendall(self.login_data_json.encode())
                    
                    logs.info(f"Connected: {self.ip}:{self.port}")
                    self.handle_server()

                    return True

            except Exception as e:
                logs.debug(f"Try connect... {e}")
                time.sleep(1)
    
    def send_to_server(self, data) -> bool:
        try:
            byte_data = data.encode()
            self.sock.sendall(byte_data)
            logs.debug(f"Msg to server: {data}")
            return True
        except Exception as e:
            logs.error(f"Sending: {data} not succeful: {e}")
            return False

    def handle_server(self):
        try:
            while self.listen:
                data = self.sock.recv(1024)
                decode_data = data.decode('utf-8', errors="ignore").strip()
                
                self.queue.put(decode_data)
                logs.debug(f"Msg from server: {decode_data}")

                if decode_data == "exit":
                    logs.warning("EXIT")
                    send_thread = t(target=self.send_to_server, args=("off",), daemon=True)
                    self.threads.append(send_thread), send_thread.start()
                    self.stop()
                elif decode_data == "*/*signed*/*":
                    logs.info("You sign to app")
                elif decode_data == "*/*registered*/*":
                    logs.info("You registered to app")

        except Exception as e:
            logs.error(f"Handle server: {e}")
        finally:
            self.connect()


def main():
    logs.basicConfig(level=logs.DEBUG, format='%(levelname)s: %(message)s')
    Client(IP, PORT).connect()

if __name__ == "__main__":
    main()