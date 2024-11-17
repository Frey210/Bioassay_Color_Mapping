import serial

def init_sensor(port, baud_rate):
    try:
        return serial.Serial(port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        return None

def read_sensor_rgb(ser):
    try:
        if ser and ser.is_open:
            ser.write(b'R')
            response = ser.readline().decode('utf-8').strip()
            return list(map(int, response.split(',')))
        return None
    except Exception as e:
        print(f"Error membaca sensor: {e}")
        return None

def close_sensor(ser):
    if ser and ser.is_open:
        ser.close()
