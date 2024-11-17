import sqlite3

# Inisialisasi dan pembuatan tabel jika belum ada
def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_rgb TEXT,
            sensor_rgb TEXT,
            density TEXT,
            image_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Menambahkan data baru ke database
def save_to_db(camera_rgb, sensor_rgb, density, image_path):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO captures (camera_rgb, sensor_rgb, density, image_path)
        VALUES (?, ?, ?, ?)
    ''', (str(camera_rgb), str(sensor_rgb), density, image_path))
    conn.commit()
    conn.close()

# Mendapatkan semua data dari database
def get_all_data():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM captures ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows
