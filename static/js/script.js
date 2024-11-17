function showSection(sectionId) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.style.display = 'none'); // Sembunyikan semua bagian
    document.getElementById(sectionId).style.display = 'block'; // Tampilkan bagian yang dipilih

    const deteksiBtn = document.getElementById('deteksiBtn');
    const riwayatBtn = document.getElementById('riwayatBtn');

    // Tambah atau hapus kelas 'active' sesuai tombol yang dipilih
    if (sectionId === 'deteksi') {
        deteksiBtn.classList.add('active');
        riwayatBtn.classList.remove('active');
    } else {
        riwayatBtn.classList.add('active');
        deteksiBtn.classList.remove('active');
    }
}

// Inisialisasi halaman saat pertama kali dimuat
document.addEventListener("DOMContentLoaded", function () {
    showSection('deteksi');
});

console.log(document.getElementById('deteksiBtn').classList);
console.log(document.getElementById('riwayatBtn').classList);

// Fungsi untuk menangkap data dari kamera dan sensor
let capturedImagePath = null;
let cameraRgb = [0, 0, 0];
let sensorRgb = [0, 0, 0];
let chart = null;

function captureData() {
    fetch('/capture', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Tampilkan gambar hasil capture
            document.getElementById('captured-image').src = data.image_path;

            // Tampilkan nilai RGB sensor
            document.getElementById('sensor-rgb').textContent = `Sensor RGB: R=${data.sensor_rgb[0]} G=${data.sensor_rgb[1]} B=${data.sensor_rgb[2]}`;
            sensorRgb = data.sensor_rgb;

            // Simpan path gambar
            capturedImagePath = data.image_path;

            // Tampilkan nilai RGB dari kamera (simulasi untuk sekarang)
            document.getElementById('camera-rgb').textContent = `Kamera RGB: R=${data.camera_rgb[0]} G=${data.camera_rgb[1]} B=${data.camera_rgb[2]}`;
            cameraRgb = data.camera_rgb;
        })
        .catch(err => console.error('Error:', err));
}

// Fungsi untuk mengirim data dan menghasilkan prediksi
function generatePrediction() {
    const bcValue = document.querySelector('input[name="bc"]:checked').value;

    fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            camera_rgb: cameraRgb,
            sensor_rgb: sensorRgb,
            bc: bcValue,
            image_path: capturedImagePath
        })
    })
        .then(response => response.json())
        .then(data => {
            // Tampilkan hasil prediksi
            document.getElementById('density-result').textContent = `${data.density} cell/ml`;

            // Update grafik dengan data baru
            updateChart();
        })
        .catch(err => console.error('Error:', err));
}

// Fungsi untuk memperbarui grafik dengan data terbaru
function updateChart() {
    fetch('/history', { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            // Ekstraksi data dari database
            const timestamps = data.map(item => item[5]); // Timestamp dari database
            const densities = data.map(item => parseFloat(item[3])); // Density value

            if (chart) {
                // Perbarui data pada grafik jika sudah ada
                chart.data.labels = timestamps;
                chart.data.datasets[0].data = densities;
                chart.update();
            } else {
                // Buat grafik baru jika belum ada
                const ctx = document.getElementById('historyChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [{
                            label: 'Kepadatan Pakan (cell/ml)',
                            data: densities,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 1,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Waktu'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Kepadatan Pakan (cell/ml)'
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error('Error:', err));
}

// Fungsi lama untuk mengirim data simulasi (masih dipertahankan)
function submitData() {
    const bcValue = document.querySelector('input[name="bc"]:checked').value;

    console.log("Nilai BC yang dipilih:", bcValue);

    const simulatedResponse = {
        density: "18 cell/ml"
    };

    document.getElementById('density-result').textContent = simulatedResponse.density;
}

// Inisialisasi halaman dan grafik saat pertama kali dimuat
document.addEventListener("DOMContentLoaded", function() {
    showSection('deteksi');
    updateChart(); // Perbarui grafik saat halaman pertama kali dimuat
});
