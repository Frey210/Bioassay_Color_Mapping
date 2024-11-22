import sqlite3
from datetime import datetime

DB_FILE = 'data.db'

def init_db():
    """Inisialisasi database jika belum ada tabel."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Membuat tabel dengan field terpisah untuk RGB dan bc_value
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            camera_r REAL NOT NULL,
            camera_g REAL NOT NULL,
            camera_b REAL NOT NULL,
            sensor_r REAL NOT NULL,
            sensor_g REAL NOT NULL,
            sensor_b REAL NOT NULL,
            bc_value INTEGER NOT NULL,
            density TEXT NOT NULL,  
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(camera_rgb, sensor_rgb, density, image_path, bc_value):
    """
    Menyimpan data ke database.
    - camera_rgb: List [r, g, b] dari kamera.
    - sensor_rgb: List [r, g, b] dari sensor.
    - density: Prediksi densitas dari model.
    - image_path: Path gambar yang disimpan.
    - bc_value: Nilai BC dari input pengguna.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Menyisipkan data ke tabel tanpa kolom 'id' (karena auto increment)
    cursor.execute('''
        INSERT INTO captures (
            timestamp, 
            camera_r, camera_g, camera_b, 
            sensor_r, sensor_g, sensor_b, 
            bc_value, density, image_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        camera_rgb[0], camera_rgb[1], camera_rgb[2],  # RGB kamera
        sensor_rgb[0], sensor_rgb[1], sensor_rgb[2],  # RGB sensor
        bc_value,
        density,
        image_path
    ))
    conn.commit()
    conn.close()

def get_all_data(limit=10):
    """Mengambil data dari database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = f'''
        SELECT 
            timestamp, 
            camera_r, camera_g, camera_b, 
            sensor_r, sensor_g, sensor_b, 
            bc_value, density, image_path 
        FROM captures 
        ORDER BY timestamp DESC 
        LIMIT {limit}
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Jika data kosong, kembalikan list kosong
    if not data:
        return []

    # Mengembalikan data dalam bentuk dictionary
    return [
        {
            "timestamp": row[0],
            "camera_rgb": [row[1], row[2], row[3]],
            "sensor_rgb": [row[4], row[5], row[6]],
            "bc_value": row[7],
            "density": row[8],  # Pastikan ini dalam format label seperti "S1", "S2"
            "image_path": row[9],
        }
        for row in data
    ]
