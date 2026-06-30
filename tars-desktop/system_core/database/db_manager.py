import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "automation_memory.db")

def get_connection():
    """Establece conexión con la base de datos y activa el soporte de claves foráneas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Crea estrictamente la estructura vacía de las 4 tablas de productividad."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        command TEXT NOT NULL,
        url TEXT,
        url_base TEXT,
        default_workspace TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        alias TEXT UNIQUE NOT NULL,
        FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS environments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS environment_apps (
        environment_id INTEGER NOT NULL,
        app_id INTEGER NOT NULL,
        workspace TEXT NOT NULL,
        PRIMARY KEY (environment_id, app_id),
        FOREIGN KEY (environment_id) REFERENCES environments(id) ON DELETE CASCADE,
        FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("» [DATABASE] Estructura relacional de 4 tablas inicializada (Vacía).")

if __name__ == "__main__":
    init_db()