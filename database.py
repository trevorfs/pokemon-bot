import sqlite3
from datetime import datetime

# Koneksi ke SQLite
conn = sqlite3.connect('pokemon.db')
cursor = conn.cursor()

# Inisialisasi tabel
def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            credits INTEGER DEFAULT 100,
            badges INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            level INTEGER,
            exp INTEGER DEFAULT 0,
            hp INTEGER,
            attack INTEGER,
            defense INTEGER,
            moves TEXT,
            is_shiny INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT,
            item_name TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_name),
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eggs (
            user_id TEXT,
            pokemon_name TEXT,
            hatch_time INTEGER,
            is_shiny INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    conn.commit()

# Auto-save data pemain baru
async def save_player_data(user_id):
    cursor.execute('SELECT * FROM players WHERE user_id = ?', (str(user_id),))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO players (user_id, credits, badges) VALUES (?, ?, ?)', (str(user_id), 100, 0))
        cursor.execute('INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, ?)', 
                      (str(user_id), 'pokeball', 5))
        conn.commit()

# Fungsi untuk menghitung EXP
def exp_for_next_level(level):
    return int(0.8 * level ** 3)

init_db()  # Inisialisasi database saat startup