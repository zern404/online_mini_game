import socket
import json
from threading import Thread as t

IP, PORT = "localhost", 6000

class Server:
    def __init__(self, ip=IP, port=PORT):
        self.ip = ip
        self.port = port

        self.s = None
        self._running = True

        self.threads = []
        self.clients = []

    def send_msg(self, client, data) -> bool:
        try:
            if self.check_client_online(client):
                client["conn"].sendall(data.encode())
                return True
            return False
        except Exception as e:
            print(f"Error in sendmsg: {e}")

    def handle_client(self, conn, addr, login_data: dict):
        print(f"Connected {addr}")

        client = {"addr": addr, "conn": conn, "login": login_data["login"], "password": login_data["password"]}
        if self.check_client_online(client):
            conn.close()
            return
        
        self.clients.append(client)
        try:
            with conn:
                while True:
                    byte_data = conn.recv(4096)
                    if not byte_data:
                        break
                    decode_data = byte_data.decode()
                    print(decode_data)
        except Exception as e:
            print(f"Error in handle client: {e}")
        finally:
            print(f"Client disconnected: {addr}")
            if client in self.clients:
                self.clients.remove(client)

    def check_client_online(self, client) -> bool:
        for c in self.clients:
            if c["addr"] == client["addr"] and c["login"] == client["login"]:
                return True
        return False

    def stop_server(self):
        self.clients.clear()
        self.threads.clear()
        self._running = False
        self.s = None

    def start_server(self):
        try:

            self.s = socket.socket()
            with self.s:
                self.s.bind((self.ip, self.port))
                self.s.listen(100)
                print(f"Server started: {self.ip}:{self.port}")
                while self._running:
                    conn, addr = self.s.accept()

                    try:
                        login_data = conn.recv(1024)
                        if not login_data:
                            print(f"No login data received from {addr}. Disconnect")
                            conn.close()
                            continue
            
                        login_data = json.loads(login_data.decode())
                    except Exception as e:
                        print(f"Invalid login data from {addr}. Disconnect")
                        conn.sendall("Invalid login data!".encode())
                        conn.close()
                        continue

                    thread_handle = t(target=self.handle_client, args=(conn, addr, login_data), daemon=True)
                    self.threads.append(thread_handle), thread_handle.start()

        except Exception as e:
            print(f"Error in start_server: {e}") 
        except KeyboardInterrupt:
            self.stop_server()
        
Server(IP, PORT).start_server()