def add_user(cursor, username, password, role):
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                   (username, password, role))

def verify_user(cursor, username, password):
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    return result[0] if result else None