import sqlite3

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  city TEXT,
                  registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  message TEXT,
                  response TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, city FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, name, city):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, name, city) VALUES (?,?,?)",
              (user_id, name, city))
    conn.commit()
    conn.close()

def log_message(user_id, user_msg, bot_resp):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message, response) VALUES (?,?,?)",
              (user_id, user_msg, bot_resp))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, name, city, registered FROM users ORDER BY registered DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_messages(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT m.timestamp, u.name, u.city, m.message, m.response
                 FROM messages m
                 JOIN users u ON m.user_id = u.user_id
                 ORDER BY m.timestamp DESC LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows