import sqlite3
import logging as logs

class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect('database.sqlite3')
        self.cursor = self.conn.cursor()

        self.create_table()
    
    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL,
            password STRING
        )
        ''')

        self.conn.commit()
    
    def create_user(self, user: dict) -> bool:
        try:
            self.cursor.execute('INSERT INTO users (login, password) VALUES (?, ?)',
                                (user["login"], user["password"]))
            logs.info(f"User: {user["login"]} succeful saved")
            return True
        except Exception as e:
            return False
        finally:
            self.conn.commit()
    
    def check_user(self, user: str) -> bool:
        login = user["login"]
        try:
            self.cursor.execute('SELECT * FROM users WHERE login = ?', (login,))
            user = self.cursor.fetchone()
            if user:
                logs.info(f"User '{login}' found")
                return True
            else:
                logs.info(f"User '{login}' not found, creating new...")
                return False
        except Exception as e:
            logs.error(f"check_user error: {e}")
            return False