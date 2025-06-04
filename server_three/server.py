import socket 
from threading import Thread as t
import logging as logs
import queue as q
import re
import json 
from colorama import Fore, init
from data.db import DataBase

IP, PORT = "localhost", 7000


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.sock = None
        self.running = True

        self.queue = q.Queue()
        self.commands = q.Queue()
        self.db = DataBase()

        self.threads = []
        self.clients = []

    def stop(self):
        logs.warning("Server stop!")
        self.sock.close()
        self.threads.clear()
        self.clients.clear()
        self.running = False

    def create_client(self, conn, addr) -> dict:
        try:
            user_data = json.loads(conn.recv(1024).decode())
            login, password, public_key = user_data["login"], user_data["password"], user_data["public_key"]
            client = {
                "conn": conn,
                "addr": addr,
                "ip": addr[0],
                "port": addr[1],
                "login": login,
                "password": password,
                "public_key": public_key
            }
            if self.db.check_user(client):
                conn.send("*/*signed*/*".encode())
                return client
            if self.db.create_user(client):
                conn.send("*/*registered*/*".encode())
                return client
        except Exception as e:
            conn.close()
            logs.debug(f"Connection {addr} close, not valid user data")

    def runserver(self):
        try:
            handle_command_thread = t(target=self.handle_command, daemon=True)
            self.threads.append(handle_command_thread)
            handle_command_thread.start()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock.bind((self.ip, self.port))
                self.sock.listen(20)
                logs.info(f"Server started: {self.ip}:{self.port}")
                while self.running:
                    try:
                        conn, addr = self.sock.accept()
                        client = self.create_client(conn, addr)
                        self.clients.append(client)
                        handle_thread = t(target=self.handle_clients, args=(client,), daemon=True)
                        self.threads.append(handle_thread)
                        handle_thread.start()
                        logs.info(f"Client connected: {addr}")
                    except Exception as e:
                        logs.error(f"accept connection {e}")
        except Exception as e:
            logs.error(f"runserver {e}")
        finally:
            self.stop()

    def check_clients_online(self, addr):
        try:
            for client in self.clients:
                if client["ip"] == addr[0] and client["port"] == addr[1]:
                    logs.debug(f"Client: {addr} founded")
                    return client
            logs.error(f"Client: {addr} not found!")
            return False
        except Exception as e:
            logs.error(f"Search client {e}")
            return False

    def send_to_client(self, data, addr, who: str):
        try:
            client = self.check_clients_online(addr)
            byte_data = data.encode()
            client["conn"].sendall(byte_data)
            logs.debug(f"Succeful sended {data} to {addr}")
            return True
        except Exception as e:
            logs.error(f"Send to:{addr} not succeful: {e}")
            return False

    def handle_clients(self, client: dict):
        conn, addr = client["conn"], client["addr"]
        try:
            with conn:
                while self.running:
                    data = conn.recv(1024)
                    decode_data = data.decode('utf-8', errors="ignore").strip()
                    logs.debug(f"Msg from {addr}: {decode_data}")
        except (ConnectionError, socket.error) as e:
            logs.error(f"Client disconnected {addr} {e}")
        except Exception as e:
            logs.error(f"runserver {addr} {e}")
        finally:
            if self.check_clients_online(client["addr"]):
                self.clients.remove(client)
            logs.debug(f"Connection: {addr} closed")


class ManageServer(Server):
    def __init__(self):
        super().__init__(IP, PORT)

        self.__commands_server = {
            "/stop": self.stop,
            "/clients": self.get_clients,
            "/remove": self.remove_client
        }

    def handle_command(self):
        while True:
            try:
                __command = input()
                for command, handler in self.__commands_server.items():
                    if __command.startswith(command):
                        data = re.search(r'\((.*?)\)', __command)
                        if data:
                            client = data.group(1)
                            handler(client)
                        else:
                            handler()
                        break
            except Exception as e:
                print(Fore.RED + f"Command: {__command} not found, error: {e}")

    def remove_client(self, login_client: str):
        try:
            for client in self.clients:
                if client["login"] == login_client:
                    conn = client["conn"]

                    conn.send("Server closed connection.".encode())
                    conn.send("exit".encode())

                    self.clients.remove(client)
                    print(Fore.GREEN + f"Client {login_client} succeful removed")
        except Exception as e:
            logs.error(f"Remove client {login_client}")

    def get_clients(self):
        if self.clients == []:
            print(Fore.RED + "No clients")
        for client in self.clients:
            print(Fore.GREEN + f"Online: {client['login']} {client['addr']}")


def main():
    init(autoreset=True)
    logs.basicConfig(level=logs.DEBUG, format='%(levelname)s: %(message)s')
    ManageServer().runserver()

if __name__ == "__main__":
    main()