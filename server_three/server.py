import socket
import json
import queue
from threading import Thread as t

IP, PORT = "localhost", 6000

command_queue = queue.Queue()
data_queue = queue.Queue()

class Server:
    def __init__(self, ip=IP, port=PORT):
        self.ip = ip
        self.port = port

        self.s = None
        self._running = True

        self.threads = []
        self.clients = []
        self.rooms = []

    def __new_thread(self, func, *args, **kwargs):
        thread = t(target=func, args=args, kwargs=kwargs, daemon=True)
        self.threads.append(thread)
        thread.start()
    
    def __kill_threads(self):
        for thread in self.threads:
            if thread.is_alive():
                if not thread.daemon:
                    thread.join(timeout=1)  
        self.threads.clear()

    def search_room(self, client):
        for room in self.rooms:
            if client["login"] in room["name"]:
                return room
        return False
    
    def remove_room(self, client) -> bool:
        try:
            room = self.search_room(client)
            if room:
                clients = room["name"].split("|")

                client1 = next((c for c in self.clients if c["login"] == clients[0]), None)
                if client1:
                    client1["in_room"] = False
                    client1["wait_room"] = False
                    room["conn1"].sendall("room closed".encode())
                else:
                    self.clients.remove(client1)

                client2 = next((c for c in self.clients if c["login"] == clients[1]), None)
                if client2:
                    client2["in_room"] = False
                    client2["wait_room"] = False
                    room["conn2"].sendall("room closed".encode())
                else:
                    self.clients.remove(client2)
                                
                self.rooms.remove(room)    
                print(f"Room: {room["name"]} has removed")
                
                return True
            return False
        except Exception as e:
            print(f"Error in remove room {e}")

    def create_room(self, client):
        print("Create")
        client = self.check_client_online(client, True)
        if client:
            for cl in self.clients:
                if cl["login"] != client["login"] and cl["in_room"] != True and cl["wait_room"] == True:
                    cl["wait_room"] = False
                    cl["in_room"] = True
                    client["wait_room"] = False
                    client["in_room"] = True   

                    room = {"name": f"{client["login"]}|{cl["login"]}", "conn1": client["conn"], "conn2": cl["conn"]}   
                    self.rooms.append(room)

                    client["conn"].sendall(f"room found! Enemy:{cl['login']}".encode())
                    cl["conn"].sendall(f"room found! Enemy:{client['login']}".encode())
                    print(f"Room created: {room['name']}")
                    return True
        return False

    def resend_data(self, client, data):
        try:
            if self.check_client_online(client):
                room = self.search_room(client)
                if room:
                    if room["conn1"] != client["conn"]:
                        room["conn1"].sendall(data)
                    else:
                        room["conn2"].sendall(data)
                else:
                    client["conn"].sendall("room not found".encode())
            else:
                self.remove_room(client)
        except Exception as e:
            print(f"Error in resend: {e}")

    def send_msg(self, client, data) -> bool:
        try:
            if self.check_client_online(client):
                client["conn"].sendall(data.encode())
                return True
            return False
        except Exception as e:
            print(f"Error in sendmsg: {e}")

    def handle_client(self, conn, addr, login_data: dict):
        print(f"Connected {addr}:{login_data["login"]}")

        client = {"addr": addr, "conn": conn, "in_room": False, "wait_room": False, "login": login_data["login"], "password": login_data["password"]}
        
        conn.sendall("connected".encode())
        self.clients.append(client)

        try:
            with conn:
                while True:
                    client = self.check_client_online(client, True)
                    byte_data = conn.recv(4096)
                    decode_data = byte_data.decode()

                    if not byte_data:
                        break
                    
                    if decode_data == "ping":
                        conn.sendall("pong".encode())

                    elif decode_data == "remove room":
                        self.remove_room(client)

                    elif decode_data == "new room":
                        if not client["in_room"]:
                            client["wait_room"] = True
                            for cl in self.clients:
                                if cl["wait_room"] and not cl["in_room"]:
                                    self.create_room(cl)

                    elif "ready" in decode_data:
                        room_check = self.search_room(client)
                        if room_check:
                            conn.sendall("start game".encode())

                    else:
                        if client["in_room"] == True:
                            self.resend_data(client, byte_data)
        except Exception as e:
            print(f"Error in handle client: {e}")
        finally:
            print(f"Client disconnected: {addr}:{client["login"]}")
            if client in self.clients:
                if client["in_room"]:
                    room = self.search_room(client)
                    if room:
                        self.remove_room(client)
                self.clients.remove(client)

    def check_client_online(self, client, get=False) -> bool:
        for c in self.clients:
            if c["addr"] == client["addr"] and c["login"] == client["login"]:
                if get:
                    return c
                return True
        return False

    def stop_server(self):
        self.clients.clear()
        self.__kill_threads()
        self._running = False
        self.s = None

    def start_server(self):
        try:

            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

                    for i in self.clients:
                        if i["login"] == login_data["login"]:
                            conn.close()
                except Exception as e:
                    print(f"Invalid login data from {addr}. Disconnect")
                    conn.sendall("Invalid login data!".encode())
                    conn.close()
                    continue
                
                self.__new_thread(self.handle_client, conn, addr, login_data)

        except Exception as e:
            print(f"Error in start_server: {e}") 
        except KeyboardInterrupt:
            self.stop_server()
        
Server(IP, PORT).start_server()