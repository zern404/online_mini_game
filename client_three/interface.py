import customtkinter as ctk
import json
import os
import queue
from client import Client
from game import Game
from threading import Thread as t

LOGIN_DATA_PATH = "client_three/configure/login_data.json"
status_queue = queue.Queue()

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Menu")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.geometry("600x500")
        self.resizable(False, False)

        self.threads = []
        self.cl = Client()

        self.main_frame = ctk.CTkFrame(self, width=600, height=500)
        self.main_frame.pack(fill="both", expand=True)

        if os.path.exists(LOGIN_DATA_PATH):
            start_client_thread = t(target=self.cl.connect_server, args=(self.read_login_data()), daemon=True)
            self.threads.append(start_client_thread), start_client_thread.start()
            self.draw_menu()
        else:
            self.draw_login()

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
    
    def clear_main_frame(self):
        self.main_frame.destroy()
        self.main_frame = ctk.CTkFrame(self, width=600, height=500)
        self.main_frame.pack(fill="both", expand=True)

    def build_json_login_data(self, login, password):
        data = {
            "login": login,
            "password": password
        }
        with open(LOGIN_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def handle_login(self, login, password):
        try:
            if login and password != None:
                self.build_json_login_data(login, password)
                self.clear_main_frame()
                self.draw_menu()
        except Exception as e:
            print(f"Error in login: {e}")

    def read_login_data(self):
        try:
            with open(LOGIN_DATA_PATH, "r", encoding="utf-8") as f:
                login_data = json.load(f)
            return login_data
        except Exception as e:
            print(f"Error reading JSON: {e}")
            return False

    def handle_singlplayer(self):
        self.destroy()
        self.cl.stop_client()
        self.game = Game(self.cl).start_singlplayer()

    def handle_online(self):
        self.destroy()
        self.game = Game(self.cl, False).start_multiplayer()

MainMenu().mainloop()