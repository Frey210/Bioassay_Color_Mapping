from flask import Flask, render_template, jsonify, request, send_from_directory
import cv2
import numpy as np
import joblib
import os
from datetime import datetime
from sensor_module import init_sensor, read_sensor_rgb, close_sensor
from database_module import init_db, save_to_db, get_all_data

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
    # Tangkap gambar dan baca data sensor
    filename, error = capture_image()
    if error:
        return jsonify({'error': error}), 500

    # Baca nilai RGB dari sensor
    sensor_rgb = read_sensor_rgb(ser) or [0, 0, 0]

    # Kembalikan path relatif dan data sensor ke frontend
    return jsonify({'image_path': f"/static/captures/{filename}", 'sensor_rgb': sensor_rgb})

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    camera_rgb = data['camera_rgb']
    sensor_rgb = data['sensor_rgb']
    bc_value = int(data.get('bc', 1))

    # Input fitur untuk prediksi model
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
def history():
    data = get_all_data()
    return jsonify(data)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Pastikan kamera dilepas dan sensor ditutup
        if camera:
            camera.release()
        close_sensor(ser)
