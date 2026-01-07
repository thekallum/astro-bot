import sqlite3
import time

def init_db():
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            verified_role_id INTEGER,
            unverified_role_id INTEGER,
            log_channel_id INTEGER,
            lockdown_enabled BOOLEAN DEFAULT FALSE
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            user_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            verification_code TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            current_input TEXT DEFAULT ''
        )
    ''')
    cur.execute('CREATE TABLE IF NOT EXISTS blocked_domains (domain TEXT PRIMARY KEY)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS verified_users (
            user_id INTEGER,
            guild_id INTEGER,
            verified_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, guild_id)
        )
    ''')
    con.commit()
    con.close()

def add_verified_user(user_id, guild_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('INSERT OR REPLACE INTO verified_users (user_id, guild_id, verified_at) VALUES (?, ?, ?)', (user_id, guild_id, int(time.time())))
    con.commit()
    con.close()

def remove_verified_user(user_id, guild_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('DELETE FROM verified_users WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
    con.commit()
    con.close()

def get_verified_user(user_id, guild_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('SELECT verified_at FROM verified_users WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
    result = cur.fetchone()
    con.close()
    return result[0] if result else None

def delete_expired_verifications():
    timeout = int(time.time()) - 3600
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('DELETE FROM verifications WHERE created_at < ?', (timeout,))
    rows_deleted = cur.rowcount
    con.commit()
    con.close()
    return rows_deleted

# Renomeei para set_settings para consistência e adicionei allowed_domains (mesmo que não esteja na tabela ainda)
# Sua função set_settings no database.py
# database.py
# ... (código anterior) ...

def set_settings(guild_id, verified_role_id, unverified_role_id, log_channel_id, allowed_domains=None):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('''
        INSERT INTO guild_settings (guild_id, verified_role_id, unverified_role_id, log_channel_id, lockdown_enabled) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
        verified_role_id = excluded.verified_role_id,
        unverified_role_id = excluded.unverified_role_id,
        log_channel_id = excluded.log_channel_id,
        lockdown_enabled = excluded.lockdown_enabled
    ''', (guild_id, verified_role_id, unverified_role_id, log_channel_id, False))
    con.commit()
    con.close()

def get_settings(guild_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('SELECT verified_role_id, unverified_role_id, log_channel_id, lockdown_enabled FROM guild_settings WHERE guild_id = ?', (guild_id,))
    settings = cur.fetchone()
    con.close()
    return settings if settings else (None, None, None, False) # Retorna 4 elementos

# ... (restante do código) ...

def set_lockdown(guild_id, status: bool):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('UPDATE guild_settings SET lockdown_enabled = ? WHERE guild_id = ?', (status, guild_id))
    con.commit()
    con.close()

def create_verification(user_id, guild_id, code):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('''
        INSERT INTO verifications (user_id, guild_id, verification_code, created_at, current_input) VALUES (?, ?, ?, ?, '')
        ON CONFLICT(user_id) DO UPDATE SET
        guild_id = excluded.guild_id,
        verification_code = excluded.verification_code,
        attempts = 0,
        created_at = excluded.created_at,
        current_input = ''
    ''', (user_id, guild_id, code, int(time.time())))
    con.commit()
    con.close()

def get_verification(user_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('SELECT guild_id, verification_code, attempts, created_at, current_input FROM verifications WHERE user_id = ?', (user_id,))
    verification = cur.fetchone()
    con.close()
    return verification

def update_attempts(user_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('UPDATE verifications SET attempts = attempts + 1 WHERE user_id = ?', (user_id,))
    con.commit()
    con.close()

def update_input_code(user_id, new_input):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('UPDATE verifications SET current_input = ? WHERE user_id = ?', (new_input, user_id))
    con.commit()
    con.close()

def delete_verification(user_id):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('DELETE FROM verifications WHERE user_id = ?', (user_id,))
    con.commit()
    con.close()

def add_blocked_domain(domain):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('INSERT OR IGNORE INTO blocked_domains (domain) VALUES (?)', (domain,))
    con.commit()
    con.close()

def remove_blocked_domain(domain):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('DELETE FROM blocked_domains WHERE domain = ?', (domain,))
    rows_affected = cur.rowcount
    con.commit()
    con.close()
    return rows_affected

def is_domain_blocked(domain):
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('SELECT 1 FROM blocked_domains WHERE domain = ?', (domain,))
    result = cur.fetchone()
    con.close()
    return result is not None

def get_all_blocked_domains():
    con = sqlite3.connect('bot.db')
    cur = con.cursor()
    cur.execute('SELECT domain FROM blocked_domains ORDER BY domain ASC')
    domains = [row[0] for row in cur.fetchall()]
    con.close()
    return domains