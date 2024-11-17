import serial

# Konfigurasi port serial
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600

# Buka port serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    print("Port serial terbuka!")
except serial.SerialException as e:
    print(f"Terjadi kesalahan saat membuka port serial: {e}")
    exit()

# Loop terus-menerus untuk membaca data
while True:
    try:
        data = ser.readline().decode('ascii').strip()
        if data:
            print(f"Data yang diterima: {data}")
    except UnicodeDecodeError:
        print("Terjadi kesalahan saat mendekode data")

# Tutup port serial (tidak akan tercapai karena loop tak terbatas)
ser.close()