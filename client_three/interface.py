import customtkinter as ctk
import json
import os
import queue
from client import Client, command_queue
from game import Game
from threading import Thread as t

LOGIN_DATA_PATH = "client_three/configure/login_data.json"
interface_queue = queue.Queue()

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Menu")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.geometry("600x500")
        self.resizable(False, False)

        self.threads = []
        self.status_connect = False

        self.status_ping_pong = False
        self.ping_ms = None

        self.byte_login_data = self.read_login_data()

        self.cl = Client()

        self.main_frame = ctk.CTkFrame(self, width=600, height=500)
        self.main_frame.pack(fill="both", expand=True)

        self.conn_lable = ctk.CTkLabel(self.main_frame, text_color="red", text="🔴 Not connected 🔴", font=("Bold", 30)) 
        self.ping_label = ctk.CTkLabel(self.main_frame, text="", font=("Bold", 20))

        self.__new_thread(self.check_status_connect)
        self.__new_thread(self.update_ping)
        self.start()

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

    def start(self):
        if os.path.exists(LOGIN_DATA_PATH):
            if self.status_connect != True:
                self.__new_thread(self.cl.connect_server, self.byte_login_data)
            self.draw_menu()
        else:
            self.draw_login()

    def check_status_connect(self):
        while True:
            try:
                try:
                    command = command_queue.get(timeout=1)
                    if command == "connected":
                        self.status_connect = True
                        self.conn_lable.configure(text_color="green", text="✅ Connected ✅")
                    elif command == "disconnected":
                        self.status_connect = False
                        self.conn_lable.configure(text_color="red", text="🔴 Not connected 🔴")
                except queue.Empty:
                    pass
                try:
                    interface_command = interface_queue.get(timeout=1)
                    if interface_command == "restart":
                        self.cl.stop_client()
                        self.main_frame.destroy()
                        self.start()
                except queue.Empty:
                    pass
            except Exception as e:
                print(f"Error in check status {e}")

    def draw_login(self):
        self.login_lable = ctk.CTkLabel(self.main_frame, text="Login", font=("Bold", 50))
        
        self.login_input = ctk.CTkEntry(self.main_frame, width=300, height=80, placeholder_text="Login", font=("Bold", 20))
        self.password_input = ctk.CTkEntry(self.main_frame, width=300, height=80, placeholder_text="Password", font=("Bold", 20))

        self.login_btn = ctk.CTkButton(self.main_frame, width=200, height=80, font=("Bold", 20), text="Login",
                                        command=lambda: self.handle_login(self.login_input.get(), self.password_input.get()))

        self.login_lable.pack(padx=10, pady=10, side="top")
        self.login_input.pack(padx=10, pady=10, side="top")
        self.password_input.pack(padx=10, pady=10, side="top")
        self.login_btn.pack(padx=10, pady=20, side="top")        

    def draw_menu(self):
        self.menu_lable = ctk.CTkLabel(self.main_frame, text="Menu", font=("Bold", 50))

        self.single_btn = ctk.CTkButton(self.main_frame, width=200, height=80, font=("Bold", 20), text="SINGLPLAYER", command=self.handle_singlplayer)
        self.online_btn = ctk.CTkButton(self.main_frame, width=200, height=80, text="2 PLAYER", font=("Bold", 20), command=self.handle_online)

        self.menu_lable.pack(padx=10, pady=40, side="top")
        self.single_btn.pack(padx=10, pady=10, side="top")
        self.online_btn.pack(padx=10, pady=10, side="top")
        self.conn_lable.pack(padx=10, pady=20, side="top")
        self.ping_label.pack(padx=10, pady=5, side="top")
    
    def clear_main_frame(self):
        self.main_frame.destroy()
        self.main_frame = ctk.CTkFrame(self, width=600, height=500)
        self.main_frame.pack(fill="both", expand=True)

    def write_json_login_data(self, login, password):
        data = {
            "login": login,
            "password": password
        }
        with open(LOGIN_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def update_ping(self):
        if self.status_connect:
            ping = self.cl.ping() 
            if ping is not None:
                self.ping_ms = ping
                self.status_ping_pong = True
                if ping >= 120:
                    self.ping_label.configure(text_color="yellow", text=f"Ping: {ping} ms")
                else:
                    self.ping_label.configure(text_color="green", text=f"Ping: {ping} ms")
            else:
                self.status_ping_pong = False
                self.ping_label.configure(text_color="red", text="Ping timeout")
        else:
            self.status_ping_pong = False
            self.ping_label.configure(text_color="red", text="")
        self.after(3000, self.update_ping)

    def read_login_data(self):
        try:
            with open(LOGIN_DATA_PATH, "r", encoding="utf-8") as f:
                login_data = json.load(f)
                json_login_data = json.dumps(login_data)
            return json_login_data.encode()
        except Exception as e:
            print(f"Error reading json: {e}")
            return False

    def handle_login(self, login, password):
        try:
            if login and password != None:
                self.write_json_login_data(login, password)
                self.clear_main_frame()
                self.draw_menu()
        except Exception as e:
            print(f"Error in login: {e}")

    def handle_singlplayer(self):
        if self.status_connect:
            self.destroy()
            self.game = Game(self.cl, self, False).run()

    def handle_online(self):
        if self.status_connect:
            self.withdraw()
            game_thread = t(target=self.start_game, daemon=True)
            game_thread.start()

    def start_game(self):
        self.game = Game(self.cl, self, False)
        self.game.run()

MainMenu().mainloop()