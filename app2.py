from flask import Flask, render_template, jsonify, request
import cv2
import numpy as np
import joblib
import os
from datetime import datetime
from sensor_module import init_sensor, read_sensor_rgb, close_sensor
from database_module import init_db, save_to_db, get_all_data
import sqlite3

app = Flask(__name__)
CAPTURE_FOLDER = os.path.join('static', 'captures')
app.config['UPLOAD_FOLDER'] = CAPTURE_FOLDER

# Buat folder jika belum ada
if not os.path.exists(CAPTURE_FOLDER):
    os.makedirs(CAPTURE_FOLDER)

# Inisialisasi Sensor
sensor_port = 'COM3'
ser = init_sensor(sensor_port, 9600)  # Inisialisasi sensor pada port serial

# Load Model Machine Learning
model_path = os.path.join('model', 'random_forest_density_modelV2.pkl')
rf_model = joblib.load(model_path)

# Inisialisasi database
init_db()

# Fungsi untuk membaca data kamera
def get_camera_rgb():
    cap = cv2.VideoCapture(0)  # Pastikan kamera terdeteksi
    ret, frame = cap.read()
    if ret:
        h, w, _ = frame.shape
        roi = frame[h//3:h//3*2, w//3:w//3*2]  # Kotak tengah
        avg_rgb = cv2.mean(roi)[:3]
        cap.release()
        # Konversi dari 0-255 ke 0-1
        return tuple(np.array(avg_rgb[:3]) / 255.0)
    else:
        cap.release()
        return (0, 0, 0)

# Fungsi untuk membaca data dari sensor
def get_sensor_rgb():
    try:
        sensor_rgb = read_sensor_rgb(ser) or [0, 0, 0]
        # Konversi dari 0-255 ke 0-1
        return tuple(np.array(sensor_rgb) / 255.0)
    except:
        return (0, 0, 0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    # Ambil RGB dari kamera dan sensor
    camera_rgb = get_camera_rgb()
    sensor_rgb = get_sensor_rgb()
    if not any(camera_rgb) or not any(sensor_rgb):
        return jsonify({'error': 'Gagal membaca data kamera atau sensor'}), 500

    # Tangkap gambar kamera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        return jsonify({'error': 'Gagal menangkap gambar'}), 500

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"capture_{timestamp}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv2.imwrite(filepath, frame)
    cap.release()

    return jsonify({
        'image_path': f"/static/captures/{filename}",
        'camera_rgb': camera_rgb,
        'sensor_rgb': sensor_rgb
    })

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    camera_rgb = data.get('camera_rgb')
    sensor_rgb = data.get('sensor_rgb')
    bc_value = int(data.get('bc', 1))  # Default bc = 1 (biru)

    if not camera_rgb or not sensor_rgb:
        return jsonify({'error': 'Data RGB tidak valid'}), 400

    # Input fitur untuk prediksi
    input_features = [
        *camera_rgb, *sensor_rgb, bc_value
    ]

    try:
        density_prediction = rf_model.predict([input_features])[0]
        # Simpan hasil ke database
        save_to_db(camera_rgb, sensor_rgb, density_prediction, data['image_path'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'density': density_prediction})

@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect('data.db')  # Ganti dengan nama database Anda
    cursor = conn.cursor()
    query = "SELECT timestamp, density FROM captures ORDER BY timestamp DESC LIMIT 10"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Ubah hasil query ke format JSON
    history = [{"timestamp": row[0], "density": row[1]} for row in data]
    return jsonify(history)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Pastikan sensor ditutup
        close_sensor(ser)
