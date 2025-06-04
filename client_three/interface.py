import customtkinter as ctk
import json
import os
from threading import Thread as t

LOGIN_DATA_PATH = "client_three/configure/login_data.json"

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Menu")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.geometry("600x500")
        self.resizable(False, False)

        self.threads = []

        self.main_frame = ctk.CTkFrame(self, width=600, height=500)
        self.main_frame.pack(fill="both", expand=True)

        if os.path.exists(LOGIN_DATA_PATH):
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
            

    def handle_singlplayer(self):
        pass

    def handle_online(self):
        pass

MainMenu().mainloop()