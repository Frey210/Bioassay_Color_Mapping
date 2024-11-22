from flask import Flask, render_template, jsonify, request, send_from_directory
import cv2
import numpy as np
import joblib
import os
from datetime import datetime
from sensor_module import init_sensor, close_sensor
from database_module import init_db, save_to_db, get_all_data
import sqlite3
import pandas as pd  # Pastikan modul Pandas diimpor



app = Flask(__name__)
CAPTURE_FOLDER = os.path.join('static', 'captures')
app.config['UPLOAD_FOLDER'] = CAPTURE_FOLDER

# Buat folder jika belum ada
if not os.path.exists(CAPTURE_FOLDER):
    os.makedirs(CAPTURE_FOLDER)

# Inisialisasi Kamera dan Sensor
camera = None
sensor_port = 'COM3'
ser = init_sensor(sensor_port, 9600)  # Inisialisasi sensor pada port serial

# Load Model Machine Learning
model_path = os.path.join('model', 'random_forest_density_modelV2.pkl')
rf_model = joblib.load(model_path)

# Inisialisasi database
init_db()

def read_camera_rgb():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)  # Inisialisasi kamera jika belum ada
    """Membaca data RGB dari kamera."""
    ret, frame = camera.read()
    if not ret:
        return [0, 0, 0]  # Return default RGB jika kamera gagal membaca
    
    h, w, _ = frame.shape
    roi = frame[h//3:h//3*2, w//3:w//3*2]  # Area tengah
    avg_rgb = cv2.mean(roi)[:3]
    return [round(c/255, 3) for c in avg_rgb]  # Normalisasi 0-1

def read_sensor_rgb():
    """Membaca data RGB dari sensor melalui Arduino."""
    try:
        arduino.write(b'READ\n')
        line = arduino.readline().decode('utf-8').strip()
        r, g, b = map(int, line.split(','))
        return [round(c/255, 3) for c in (r, g, b)]  # Normalisasi 0-1
    except:
        return [0.647058823529412, 0.505882352941176, 0.356862745098039]  # Return default RGB jika gagal membaca
        print("cek koneksi arduino")

# Fungsi untuk menangkap gambar kamera
def capture_image():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)  # Inisialisasi kamera jika belum ada

    ret, frame = camera.read()
    if not ret:
        return None, "Error: Tidak dapat menangkap gambar."

    # Simpan gambar ke folder dengan nama berbasis timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"capture_{timestamp}.png"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv2.imwrite(file_path, frame)

    # Tutup kamera setelah digunakan
    camera.release()
    camera = None

    return filename, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    """Mengambil data dari kamera dan sensor, lalu menyimpan gambar."""
    try:
        # Baca data RGB dari kamera
        camera_rgb = read_camera_rgb()
        sensor_rgb = read_sensor_rgb()

        global camera
        if camera is None:
            camera = cv2.VideoCapture(0)  # Inisialisasi kamera jika belum ada 
        # Ambil gambar dari kamera
        ret, frame = camera.read()
        if not ret:
            return jsonify({"error": "Failed to capture image from camera"}), 500

        # Simpan gambar ke direktori
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = f"capture_{timestamp}.jpg"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
        cv2.imwrite(image_path, frame)
        camera.release()
        camera = None

        # Kirimkan path gambar relatif ke `static` untuk frontend
        return jsonify({
            "camera_rgb": camera_rgb,
            "sensor_rgb": sensor_rgb,  # Contoh nilai sementara
            "image_path": f"/{image_path}"  # Path relatif
        })

    except Exception as e:
        # Tulis error ke log dan kembalikan respons error
        print(f"Error in /capture: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    camera_rgb = data['camera_rgb']
    sensor_rgb = data['sensor_rgb']
    bc_value = int(data.get('bc', 1))

    print("Camera RGB:", camera_rgb)
    print("Sensor RGB:", sensor_rgb)
    print("BC value:", bc_value)

    # Pastikan fitur sesuai format model
    feature_columns = ['Cam_R', 'Cam_G', 'Cam_B', 'Sensor_R', 'Sensor_G', 'Sensor_B', 'BC']
    input_features = pd.DataFrame(
        data=[[camera_rgb[0], camera_rgb[1], camera_rgb[2], sensor_rgb[0], sensor_rgb[1], sensor_rgb[2], bc_value]],
        columns=feature_columns
    )
    print("Input features DataFrame:")
    print(input_features)
    print("Columns in input features:", input_features.columns)

    try:
        # Melakukan prediksi dengan memastikan nama kolom pada input_features
        density_prediction = rf_model.predict(input_features)[0]
        print(density_prediction)
        # Simpan hasil ke database
        save_to_db(camera_rgb, sensor_rgb, density_prediction, data['image_path'], bc_value)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'density': density_prediction})


@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect('data.db')  # Ganti dengan nama database Anda
    cursor = conn.cursor()
    query = "SELECT * FROM captures ORDER BY timestamp DESC LIMIT 10"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Ubah hasil query ke format JSON
    # Mengubah data ke dalam format yang sesuai untuk dikirim ke frontend
    history = []
    for row in data:
        history.append({
            'timestamp': row[1],
            'camera_rgb': [row[2], row[3], row[4]],
            'sensor_rgb': [row[5], row[6], row[7]],
            'bc_value': row[8],
            'density': row[9],
            'image_path': row[10]
        })
    return jsonify(history)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Pastikan kamera dilepas dan sensor ditutup
        if camera:
            camera.release()
        close_sensor(ser)
