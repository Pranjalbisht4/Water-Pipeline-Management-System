import sqlite3
from config import DATABASE_NAME

def get_connection():
    return sqlite3.connect(DATABASE_NAME, check_same_thread=False)

def setup_database(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leak_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT,
                        destination TEXT,
                        timestamp TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT CHECK(role IN ('admin', 'user')))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pipes (
                        source TEXT,
                        destination TEXT,
                        capacity INTEGER,
                        cost INTEGER,
                        leak BOOLEAN DEFAULT 0)''')

    conn.commit()